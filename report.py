from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path


def safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def format_number(value) -> str:
    return f"{safe_int(value):,}"


def create_report(result, report_path):
    output_path = Path(result["output_path"])
    report_path = Path(report_path)

    month = str(result.get("month", "")).strip()
    success_files = result.get("success_files", []) or []
    failed_files = result.get("failed_files", []) or []
    warnings = result.get("warnings", []) or []

    total_files = safe_int(result.get("total_detected_files"))
    if total_files == 0:
        total_files = len(success_files) + len(failed_files)

    success_count = len(success_files)
    failed_count = len(failed_files)

    success_rate = (
        round((success_count / total_files) * 100, 1)
        if total_files
        else 0
    )

    total_transferred = sum(
        safe_int(item.get("transferred_cells"))
        for item in success_files
        if isinstance(item, dict)
    )

    total_empty = sum(
        safe_int(item.get("empty_cells_count"))
        for item in success_files
        if isinstance(item, dict)
    )

    # ========================================
    # ملخص حالات الملفات
    # ========================================

    status_counts = {
        "Applicable": 0,
        "Not Applicable": 0,
        "No Cases": 0,
    }

    for item in success_files:
        if not isinstance(item, dict):
            continue

        status = str(item.get("status") or "").strip()
        if status in status_counts:
            status_counts[status] += 1

    # ========================================
    # ملخص حسب الـ Domain
    # ========================================

    domain_summary = defaultdict(
        lambda: {
            "files": 0,
            "successful": 0,
            "failed": 0,
            "transferred": 0,
            "empty": 0,
            "applicable": 0,
            "not_applicable": 0,
            "no_cases": 0,
        }
    )

    for item in success_files:
        if not isinstance(item, dict):
            continue

        domain = str(item.get("domain") or "غير محدد").strip()

        domain_summary[domain]["files"] += 1
        domain_summary[domain]["successful"] += 1
        domain_summary[domain]["transferred"] += safe_int(
            item.get("transferred_cells")
        )
        domain_summary[domain]["empty"] += safe_int(
            item.get("empty_cells_count")
        )

        status = str(item.get("status") or "").strip()
        if status == "Applicable":
            domain_summary[domain]["applicable"] += 1
        elif status == "Not Applicable":
            domain_summary[domain]["not_applicable"] += 1
        elif status == "No Cases":
            domain_summary[domain]["no_cases"] += 1

    for item in failed_files:
        if not isinstance(item, dict):
            continue

        domain = str(item.get("domain") or "غير محدد").strip()

        domain_summary[domain]["files"] += 1
        domain_summary[domain]["failed"] += 1

    domain_rows = []

    for domain, values in sorted(domain_summary.items()):
        domain_total = values["files"]

        domain_rate = (
            round(
                (values["successful"] / domain_total) * 100,
                1,
            )
            if domain_total
            else 0
        )

        domain_rows.append(
            f"""
            <tr>
                <td class="domain-name">{escape(domain)}</td>
                <td>{format_number(values["files"])}</td>
                <td class="success-text">
                    {format_number(values["successful"])}
                </td>
                <td class="danger-text">
                    {format_number(values["failed"])}
                </td>
                <td>{format_number(values["applicable"])}</td>
                <td>{format_number(values["not_applicable"])}</td>
                <td>{format_number(values["no_cases"])}</td>
                <td>{format_number(values["transferred"])}</td>
                <td class="warning-text">
                    {format_number(values["empty"])}
                </td>
                <td>
                    <div class="mini-progress">
                        <div
                            class="mini-progress-value"
                            style="width: {domain_rate}%"
                        ></div>
                    </div>
                    <span class="rate-text">{domain_rate}%</span>
                </td>
            </tr>
            """
        )

    if not domain_rows:
        domain_rows.append(
            """
            <tr>
                <td colspan="10" class="empty-message">
                    لا توجد بيانات
                </td>
            </tr>
            """
        )

    # ========================================
    # الملفات التي تحتاج مراجعة
    # ========================================

    review_files = []

    for item in success_files:
        if not isinstance(item, dict):
            continue

        empty_count = safe_int(item.get("empty_cells_count"))

        if empty_count <= 0:
            continue

        transferred = safe_int(item.get("transferred_cells"))
        total_cells = transferred + empty_count

        completion_rate = (
            round((transferred / total_cells) * 100, 1)
            if total_cells
            else 0
        )

        review_files.append(
            {
                "file": str(item.get("file") or ""),
                "domain": str(item.get("domain") or ""),
                "facility_code": str(
                    item.get("facility_code") or ""
                ),
                "status": str(item.get("status") or ""),
                "transferred": transferred,
                "empty": empty_count,
                "completion_rate": completion_rate,
            }
        )

    review_files.sort(
        key=lambda item: item["empty"],
        reverse=True,
    )

    review_rows = []

    for item in review_files:
        severity_class = "medium-badge"

        if item["completion_rate"] < 50:
            severity_class = "high-badge"
        elif item["completion_rate"] >= 90:
            severity_class = "low-badge"

        review_rows.append(
            f"""
            <tr class="review-row">
                <td class="file-name">
                    {escape(item["file"])}
                </td>
                <td>{escape(item["domain"])}</td>
                <td>{escape(item["facility_code"])}</td>
                <td>{escape(item["status"])}</td>
                <td>{format_number(item["transferred"])}</td>
                <td class="warning-text">
                    {format_number(item["empty"])}
                </td>
                <td>
                    <span class="status-badge {severity_class}">
                        {item["completion_rate"]}%
                    </span>
                </td>
            </tr>
            """
        )

    if not review_rows:
        review_rows.append(
            """
            <tr>
                <td colspan="7" class="empty-message">
                    ممتاز، لا توجد ملفات تحتوي على خلايا فارغة.
                </td>
            </tr>
            """
        )

    # ========================================
    # الملفات الفاشلة
    # ========================================

    failed_rows = []

    for item in failed_files:
        if isinstance(item, dict):
            file_name = str(item.get("file") or "")
            domain = str(item.get("domain") or "")
            error = str(item.get("error") or "")
        else:
            file_name = str(item)
            domain = ""
            error = ""

        failed_rows.append(
            f"""
            <tr>
                <td class="file-name">{escape(file_name)}</td>
                <td>{escape(domain)}</td>
                <td class="error-message">{escape(error)}</td>
            </tr>
            """
        )

    if not failed_rows:
        failed_rows.append(
            """
            <tr>
                <td colspan="3" class="empty-message success-message">
                    لا توجد ملفات فاشلة.
                </td>
            </tr>
            """
        )

    # ========================================
    # تفاصيل التحذيرات
    # ========================================

    warning_rows = []

    for item in warnings:
        if not isinstance(item, dict):
            warning_rows.append(
                f"""
                <tr>
                    <td colspan="6">{escape(str(item))}</td>
                </tr>
                """
            )
            continue

        warning_rows.append(
            f"""
            <tr>
                <td class="file-name">
                    {escape(str(item.get("file") or ""))}
                </td>
                <td>
                    {escape(str(item.get("domain") or ""))}
                </td>
                <td>
                    {escape(str(item.get("sheet") or ""))}
                </td>
                <td>
                    {escape(str(item.get("source_cell") or ""))}
                </td>
                <td>
                    {escape(str(item.get("target_cell") or ""))}
                </td>
                <td>
                    {escape(str(item.get("warning") or ""))}
                </td>
            </tr>
            """
        )

    if not warning_rows:
        warning_rows.append(
            """
            <tr>
                <td colspan="6" class="empty-message success-message">
                    لا توجد تحذيرات.
                </td>
            </tr>
            """
        )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير استيراد مؤشرات الجودة | Quality Indicators Import Report</title>

    <style>
        :root {{
            --navy-950: #071b2a;
            --navy-900: #0b2639;
            --navy-800: #12364c;
            --navy-700: #1b4b65;
            --teal-700: #0f625f;
            --teal-600: #147a75;
            --gold-600: #a9823b;
            --gold-500: #c3a15d;
            --sand-100: #f5f1e8;
            --green-700: #17633c;
            --green-100: #e8f3ec;
            --red-700: #9f2f2f;
            --red-100: #f8eaea;
            --amber-700: #946113;
            --amber-100: #fbf1da;
            --ink: #18232d;
            --muted: #66737e;
            --line: #d9e0e5;
            --surface: #ffffff;
            --page: #edf1f3;
            --shadow: 0 16px 42px rgba(7, 27, 42, 0.10);
        }}

        * {{
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            margin: 0;
            color: var(--ink);
            background:
                linear-gradient(rgba(237, 241, 243, 0.94), rgba(237, 241, 243, 0.94)),
                repeating-linear-gradient(
                    45deg,
                    rgba(11, 38, 57, 0.025) 0,
                    rgba(11, 38, 57, 0.025) 1px,
                    transparent 1px,
                    transparent 10px
                );
            font-family: "Segoe UI", Tahoma, Arial, sans-serif;
            line-height: 1.6;
        }}

        button,
        input {{
            font: inherit;
        }}

        .page-shell {{
            width: min(1500px, calc(100% - 36px));
            margin: 28px auto 38px;
        }}

        .official-header {{
            overflow: hidden;
            color: #ffffff;
            background:
                linear-gradient(115deg, var(--navy-950) 0%, var(--navy-900) 52%, var(--teal-700) 100%);
            border: 1px solid rgba(195, 161, 93, 0.42);
            border-radius: 4px;
            box-shadow: var(--shadow);
        }}

        .gold-line {{
            height: 5px;
            background: linear-gradient(90deg, var(--gold-600), #e1c98c, var(--gold-600));
        }}

        .header-main {{
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 24px;
            padding: 24px 30px;
        }}

        .identity-mark {{
            width: 78px;
            height: 78px;
            display: grid;
            place-items: center;
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.07);
            box-shadow: inset 0 0 0 5px rgba(195, 161, 93, 0.10);
        }}

        .identity-mark svg {{
            width: 52px;
            height: 52px;
            fill: none;
            stroke: #e5ce93;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}

        .identity-copy {{
            min-width: 0;
        }}

        .authority-ar {{
            display: block;
            margin-bottom: 3px;
            color: #ffffff;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 0.1px;
        }}

        .authority-en {{
            display: block;
            color: rgba(255, 255, 255, 0.76);
            font-size: 12px;
            letter-spacing: 1.1px;
            text-transform: uppercase;
            direction: ltr;
            text-align: right;
        }}

        .document-class {{
            min-width: 190px;
            padding: 12px 16px;
            border-right: 3px solid var(--gold-500);
            background: rgba(0, 0, 0, 0.13);
        }}

        .document-class span {{
            display: block;
            color: rgba(255, 255, 255, 0.66);
            font-size: 11px;
        }}

        .document-class strong {{
            display: block;
            margin-top: 2px;
            color: #ffffff;
            font-size: 14px;
        }}

        .report-hero {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 24px;
            align-items: end;
            padding: 28px 30px 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(0, 0, 0, 0.10);
        }}

        .report-title .overline {{
            display: block;
            margin-bottom: 8px;
            color: #e4cd94;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.6px;
        }}

        .report-title h1 {{
            margin: 0;
            color: #ffffff;
            font-size: clamp(28px, 4vw, 44px);
            line-height: 1.22;
        }}

        .report-title h1 small {{
            display: block;
            margin-top: 8px;
            color: rgba(255, 255, 255, 0.70);
            font-size: 15px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }}

        .report-meta {{
            display: grid;
            grid-template-columns: repeat(3, minmax(150px, 1fr));
            gap: 1px;
            background: rgba(255, 255, 255, 0.17);
            border: 1px solid rgba(255, 255, 255, 0.17);
        }}

        .meta-item {{
            min-height: 78px;
            padding: 13px 16px;
            background: rgba(7, 27, 42, 0.72);
        }}

        .meta-item span {{
            display: block;
            color: rgba(255, 255, 255, 0.58);
            font-size: 10px;
            line-height: 1.35;
        }}

        .meta-item strong {{
            display: block;
            margin-top: 7px;
            color: #ffffff;
            font-size: 13px;
            overflow-wrap: anywhere;
        }}

        .content {{
            margin-top: 22px;
        }}

        .section {{
            margin-bottom: 20px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 4px;
            box-shadow: 0 8px 24px rgba(7, 27, 42, 0.055);
        }}

        .section-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 17px 20px;
            border-bottom: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff, #f7f9fa);
        }}

        .section-title {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
            color: var(--navy-900);
            font-size: 18px;
        }}

        .section-title::before {{
            content: "";
            width: 4px;
            height: 30px;
            background: linear-gradient(var(--gold-500), var(--gold-600));
        }}

        .section-title span {{
            display: block;
        }}

        .section-title small {{
            display: block;
            margin-top: 1px;
            color: var(--muted);
            font-size: 11px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }}

        .section-body {{
            padding: 20px;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            position: relative;
            min-height: 140px;
            padding: 19px;
            overflow: hidden;
            background: #ffffff;
            border: 1px solid var(--line);
            border-top: 4px solid var(--navy-700);
            box-shadow: 0 6px 18px rgba(7, 27, 42, 0.05);
        }}

        .stat-card::after {{
            content: "";
            position: absolute;
            width: 95px;
            height: 95px;
            left: -36px;
            bottom: -42px;
            border: 1px solid rgba(11, 38, 57, 0.08);
            transform: rotate(45deg);
        }}

        .stat-card.success {{ border-top-color: var(--green-700); }}
        .stat-card.danger {{ border-top-color: var(--red-700); }}
        .stat-card.warning {{ border-top-color: var(--amber-700); }}
        .stat-card.gold {{ border-top-color: var(--gold-600); }}

        .stat-label-ar {{
            display: block;
            color: var(--navy-900);
            font-size: 13px;
            font-weight: 750;
        }}

        .stat-label-en {{
            display: block;
            margin-top: 1px;
            color: var(--muted);
            font-size: 10px;
            direction: ltr;
            text-align: right;
        }}

        .stat-value {{
            display: block;
            margin-top: 16px;
            color: var(--ink);
            font-size: 32px;
            font-weight: 800;
            line-height: 1;
            direction: ltr;
            text-align: right;
        }}

        .performance-grid {{
            display: grid;
            grid-template-columns: 1.4fr 0.6fr;
            gap: 20px;
            align-items: center;
        }}

        .progress-shell {{
            position: relative;
            height: 22px;
            overflow: hidden;
            background: #e4e9ec;
            border: 1px solid #d5dde2;
        }}

        .progress-value {{
            height: 100%;
            background: linear-gradient(90deg, var(--teal-700), var(--teal-600));
        }}

        .progress-caption {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            margin-top: 12px;
            color: var(--muted);
            font-size: 13px;
        }}

        .progress-caption strong {{
            color: var(--navy-900);
        }}

        .performance-score {{
            padding: 18px;
            text-align: center;
            background: var(--navy-900);
            border-bottom: 4px solid var(--gold-500);
        }}

        .performance-score span {{
            display: block;
            color: rgba(255, 255, 255, 0.66);
            font-size: 11px;
        }}

        .performance-score strong {{
            display: block;
            margin: 4px 0;
            color: #ffffff;
            font-size: 38px;
            line-height: 1.1;
            direction: ltr;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            min-width: 830px;
            border-collapse: collapse;
        }}

        th {{
            padding: 13px 12px;
            color: #ffffff;
            background: var(--navy-800);
            border-left: 1px solid rgba(255, 255, 255, 0.10);
            font-size: 12px;
            text-align: right;
            vertical-align: bottom;
        }}

        th small {{
            display: block;
            margin-top: 2px;
            color: rgba(255, 255, 255, 0.62);
            font-size: 9px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e3e8eb;
            border-left: 1px solid #edf0f2;
            font-size: 13px;
            vertical-align: middle;
        }}

        tbody tr:nth-child(even) {{
            background: #f8fafb;
        }}

        tbody tr:hover {{
            background: #eef5f4;
        }}

        .file-name {{
            direction: ltr;
            text-align: left;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12px;
        }}

        .domain-name {{
            color: var(--navy-800);
            font-weight: 750;
        }}

        .success-text {{ color: var(--green-700); font-weight: 750; }}
        .danger-text {{ color: var(--red-700); font-weight: 750; }}
        .warning-text {{ color: var(--amber-700); font-weight: 750; }}
        .error-message {{ color: var(--red-700); }}

        .mini-progress {{
            width: 100px;
            height: 7px;
            display: inline-block;
            overflow: hidden;
            vertical-align: middle;
            background: #dfe5e8;
        }}

        .mini-progress-value {{
            height: 100%;
            background: var(--teal-600);
        }}

        .rate-text {{
            display: inline-block;
            min-width: 52px;
            margin-right: 8px;
            color: var(--navy-900);
            font-weight: 700;
            direction: ltr;
        }}

        .status-badge {{
            display: inline-block;
            min-width: 70px;
            padding: 5px 10px;
            border: 1px solid transparent;
            text-align: center;
            font-size: 11px;
            font-weight: 800;
            direction: ltr;
        }}

        .high-badge {{ color: var(--red-700); background: var(--red-100); border-color: #eccaca; }}
        .medium-badge {{ color: var(--amber-700); background: var(--amber-100); border-color: #ead8ac; }}
        .low-badge {{ color: var(--green-700); background: var(--green-100); border-color: #cbe2d3; }}

        .empty-message {{
            padding: 28px;
            color: var(--muted);
            text-align: center;
        }}

        .success-message {{ color: var(--green-700); }}

        .toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 16px;
        }}

        .search-input {{
            width: min(430px, 100%);
            padding: 11px 13px;
            color: var(--ink);
            background: #ffffff;
            border: 1px solid #bdc8cf;
            border-radius: 2px;
            outline: none;
        }}

        .search-input:focus {{
            border-color: var(--teal-700);
            box-shadow: 0 0 0 3px rgba(15, 98, 95, 0.10);
        }}

        .count-label {{
            padding: 9px 13px;
            color: var(--navy-900);
            background: var(--sand-100);
            border-right: 3px solid var(--gold-600);
            font-size: 12px;
        }}

        details {{
            border: 1px solid var(--line);
        }}

        summary {{
            cursor: pointer;
            padding: 15px 17px;
            color: var(--navy-900);
            background: #f5f7f8;
            font-weight: 750;
        }}

        details[open] summary {{
            border-bottom: 1px solid var(--line);
        }}

        details .table-wrapper {{
            padding: 12px;
        }}

        .report-footer {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 20px;
            align-items: center;
            padding: 18px 22px;
            color: #ffffff;
            background: var(--navy-950);
            border-top: 4px solid var(--gold-600);
            font-size: 11px;
        }}

        .report-footer span {{
            display: block;
        }}

        .report-footer small {{
            display: block;
            color: rgba(255, 255, 255, 0.56);
            direction: ltr;
            text-align: right;
        }}

        .confidential {{
            padding: 7px 10px;
            color: #e5ce93;
            border: 1px solid rgba(229, 206, 147, 0.48);
            letter-spacing: 0.8px;
            white-space: nowrap;
        }}

        @media (max-width: 1100px) {{
            .header-main {{
                grid-template-columns: auto 1fr;
            }}

            .document-class {{
                grid-column: 1 / -1;
            }}

            .report-hero {{
                grid-template-columns: 1fr;
            }}

            .report-meta {{
                grid-template-columns: repeat(3, 1fr);
            }}

            .cards {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 720px) {{
            .page-shell {{
                width: min(100% - 18px, 1500px);
                margin-top: 9px;
            }}

            .header-main {{
                grid-template-columns: 1fr;
                text-align: center;
            }}

            .identity-mark {{
                margin: 0 auto;
            }}

            .authority-en {{
                text-align: center;
            }}

            .document-class {{
                border-right: 0;
                border-top: 3px solid var(--gold-500);
            }}

            .report-hero {{
                padding: 22px 18px;
            }}

            .report-title h1 small {{
                text-align: right;
            }}

            .report-meta {{
                grid-template-columns: 1fr;
            }}

            .cards {{
                grid-template-columns: 1fr;
            }}

            .performance-grid {{
                grid-template-columns: 1fr;
            }}

            .section-head,
            .toolbar {{
                align-items: stretch;
                flex-direction: column;
            }}

            .section-body {{
                padding: 13px;
            }}

            .report-footer {{
                grid-template-columns: 1fr;
                text-align: center;
            }}

            .report-footer small {{
                text-align: center;
            }}
        }}

        @media print {{
            @page {{
                size: A4 landscape;
                margin: 10mm;
            }}

            body {{
                background: #ffffff;
            }}

            .page-shell {{
                width: 100%;
                margin: 0;
            }}

            .official-header,
            .section,
            .stat-card {{
                box-shadow: none;
            }}

            .search-input {{
                display: none;
            }}

            .section,
            .stat-card {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>

<body>
    <div class="page-shell">
        <header class="official-header">
            <div class="gold-line"></div>

            <div class="header-main">
                <div class="identity-mark" aria-hidden="true">
                    <svg viewBox="0 0 64 64">
                        <path d="M32 6l18 8v14c0 13-7.7 23.5-18 29-10.3-5.5-18-16-18-29V14z"></path>
                        <path d="M32 18v26M19 31h26"></path>
                        <path d="M26 13h12M26 49h12"></path>
                    </svg>
                </div>

                <div class="identity-copy">
                    <span class="authority-ar">منظومة الخدمات الصحية المؤسسية</span>
                    <span class="authority-en">Institutional Healthcare Services System</span>
                </div>

                <div class="document-class">
                    <span>تصنيف الوثيقة | Document Classification</span>
                    <strong>تقرير تشغيلي داخلي | Internal Operational Report</strong>
                </div>
            </div>

            <div class="report-hero">
                <div class="report-title">
                    <span class="overline">إدارة الجودة وسلامة المرضى | Quality & Patient Safety Department</span>
                    <h1>
                        تقرير استيراد مؤشرات الجودة
                        <small>Quality Indicators Import Report</small>
                    </h1>
                </div>

                <div class="report-meta">
                    <div class="meta-item">
                        <span>الملف الناتج<br>Output File</span>
                        <strong>{escape(output_path.name)}</strong>
                    </div>
                    <div class="meta-item">
                        <span>فترة التقرير<br>Reporting Period</span>
                        <strong>{escape(month or "غير محدد | Not Specified")}</strong>
                    </div>
                    <div class="meta-item">
                        <span>تاريخ الإصدار<br>Issue Date</span>
                        <strong>{generated_at}</strong>
                    </div>
                </div>
            </div>
        </header>

        <main class="content">
            <section class="cards" aria-label="ملخص المؤشرات">
                <article class="stat-card">
                    <span class="stat-label-ar">إجمالي الملفات</span>
                    <span class="stat-label-en">Total Files</span>
                    <strong class="stat-value">{format_number(total_files)}</strong>
                </article>

                <article class="stat-card success">
                    <span class="stat-label-ar">تم الاستيراد بنجاح</span>
                    <span class="stat-label-en">Successfully Imported</span>
                    <strong class="stat-value">{format_number(success_count)}</strong>
                </article>

                <article class="stat-card danger">
                    <span class="stat-label-ar">الملفات الفاشلة</span>
                    <span class="stat-label-en">Failed Files</span>
                    <strong class="stat-value">{format_number(failed_count)}</strong>
                </article>

                <article class="stat-card gold">
                    <span class="stat-label-ar">نسبة نجاح الاستيراد</span>
                    <span class="stat-label-en">Import Success Rate</span>
                    <strong class="stat-value">{success_rate}%</strong>
                </article>

                <article class="stat-card success">
                    <span class="stat-label-ar">الخلايا المنقولة</span>
                    <span class="stat-label-en">Transferred Cells</span>
                    <strong class="stat-value">{format_number(total_transferred)}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">الخلايا الفارغة</span>
                    <span class="stat-label-en">Empty Cells</span>
                    <strong class="stat-value">{format_number(total_empty)}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">ملفات تحتاج مراجعة</span>
                    <span class="stat-label-en">Files Requiring Review</span>
                    <strong class="stat-value">{format_number(len(review_files))}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">إجمالي التحذيرات</span>
                    <span class="stat-label-en">Total Warnings</span>
                    <strong class="stat-value">{format_number(len(warnings))}</strong>
                </article>

                <article class="stat-card success">
                    <span class="stat-label-ar">قابل للتطبيق</span>
                    <span class="stat-label-en">Applicable</span>
                    <strong class="stat-value">{format_number(status_counts["Applicable"])}</strong>
                </article>

                <article class="stat-card gold">
                    <span class="stat-label-ar">غير قابل للتطبيق</span>
                    <span class="stat-label-en">Not Applicable</span>
                    <strong class="stat-value">{format_number(status_counts["Not Applicable"])}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">لا توجد حالات</span>
                    <span class="stat-label-en">No Cases</span>
                    <strong class="stat-value">{format_number(status_counts["No Cases"])}</strong>
                </article>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            مؤشر الأداء العام
                            <small>Overall Import Performance</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body performance-grid">
                    <div>
                        <div class="progress-shell">
                            <div class="progress-value" style="width: {success_rate}%"></div>
                        </div>
                        <div class="progress-caption">
                            <span>
                                تم استيراد <strong>{success_count}</strong> من أصل
                                <strong>{total_files}</strong> ملف
                                &nbsp;|&nbsp;
                                <span dir="ltr">{success_count} of {total_files} files imported</span>
                            </span>
                        </div>
                    </div>

                    <div class="performance-score">
                        <span>نسبة النجاح | Success Rate</span>
                        <strong>{success_rate}%</strong>
                        <span>النتيجة التشغيلية | Operational Result</span>
                    </div>
                </div>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            ملخص الأقسام
                            <small>Domain Summary</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>القسم<small>Domain</small></th>
                                <th>إجمالي الملفات<small>Total Files</small></th>
                                <th>ناجح<small>Successful</small></th>
                                <th>فاشل<small>Failed</small></th>
                                <th>قابل للتطبيق<small>Applicable</small></th>
                                <th>غير قابل للتطبيق<small>Not Applicable</small></th>
                                <th>لا توجد حالات<small>No Cases</small></th>
                                <th>الخلايا المنقولة<small>Transferred Cells</small></th>
                                <th>الخلايا الفارغة<small>Empty Cells</small></th>
                                <th>نسبة النجاح<small>Success Rate</small></th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(domain_rows)}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            الملفات الفاشلة
                            <small>Failed Files</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>اسم الملف<small>File Name</small></th>
                                <th>القسم<small>Domain</small></th>
                                <th>سبب الفشل<small>Failure Reason</small></th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(failed_rows)}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            الملفات التي تحتاج مراجعة
                            <small>Files Requiring Review</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body">
                    <div class="toolbar">
                        <input
                            id="reviewSearch"
                            class="search-input"
                            type="text"
                            placeholder="ابحث باسم الملف أو القسم | Search by file name or domain"
                            onkeyup="filterReviewTable()"
                        >

                        <div class="count-label">
                            عدد الملفات | File Count:
                            <strong>{len(review_files)}</strong>
                        </div>
                    </div>

                    <div class="table-wrapper">
                        <table id="reviewTable">
                            <thead>
                                <tr>
                                    <th>اسم الملف<small>File Name</small></th>
                                    <th>القسم<small>Domain</small></th>
                                    <th>كود المنشأة<small>Facility Code</small></th>
                                    <th>الحالة<small>Status</small></th>
                                    <th>الخلايا المنقولة<small>Transferred Cells</small></th>
                                    <th>الخلايا الفارغة<small>Empty Cells</small></th>
                                    <th>نسبة الاكتمال<small>Completion Rate</small></th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(review_rows)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <section class="section">
                <div class="section-body">
                    <details>
                        <summary>
                            عرض التفاصيل الفنية للتحذيرات
                            | View Technical Warning Details
                            ({format_number(len(warnings))})
                        </summary>

                        <div class="table-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>اسم الملف<small>File Name</small></th>
                                        <th>القسم<small>Domain</small></th>
                                        <th>ورقة العمل<small>Worksheet</small></th>
                                        <th>خلية المصدر<small>Source Cell</small></th>
                                        <th>خلية الهدف<small>Target Cell</small></th>
                                        <th>التحذير<small>Warning</small></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(warning_rows)}
                                </tbody>
                            </table>
                        </div>
                    </details>
                </div>
            </section>
        </main>

        <footer class="report-footer">
            <div>
                <span>تم إنشاء هذا التقرير آليًا بواسطة نظام استيراد مؤشرات الجودة.</span>
                <small>This report was generated automatically by the Quality Indicators Import System.</small>
            </div>
            <div class="confidential">للاستخدام الداخلي | INTERNAL USE</div>
        </footer>
    </div>

    <script>
        function filterReviewTable() {{
            const input = document
                .getElementById("reviewSearch")
                .value
                .toLowerCase();

            const rows = document.querySelectorAll(
                "#reviewTable tbody .review-row"
            );

            rows.forEach(function(row) {{
                const text = row.innerText.toLowerCase();

                row.style.display = text.includes(input)
                    ? ""
                    : "none";
            }});
        }}
    </script>
</body>
</html>
"""

    report_path.write_text(
        html_content,
        encoding="utf-8",
    )