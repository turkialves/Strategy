from __future__ import annotations

from collections import Counter
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


def _as_list(value):
    return value if isinstance(value, list) else []


def _text(value) -> str:
    return str(value or "").strip()


def create_hqi_report(result, report_path):
    """
    إنشاء تقرير HTML خاص بعملية HQI.

    المفاتيح المدعومة داخل result:
    - output_path
    - month
    - total_files / total_detected_files
    - transferred / transferred_rows / success_files
    - missing_hospitals
    - month_mismatches / month_mismatch
    - duplicates
    - skipped_files / skipped
    - errors / failed_files
    - warnings
    """

    report_path = Path(report_path)
    output_path = Path(result.get("output_path") or "HQI_Master_Output.xlsx")
    month = _text(result.get("month"))

    transferred = _as_list(
        result.get("transferred")
        or result.get("transferred_rows")
        or result.get("success_files")
    )

    missing_hospitals = _as_list(result.get("missing_hospitals"))

    month_mismatches = _as_list(
        result.get("month_mismatches")
        or result.get("month_mismatch")
    )

    duplicates = _as_list(result.get("duplicates"))

    skipped_files = _as_list(
        result.get("skipped_files")
        or result.get("skipped")
    )

    errors = _as_list(
        result.get("errors")
        or result.get("failed_files")
    )

    warnings = _as_list(result.get("warnings"))

    total_files = safe_int(
        result.get("total_files")
        or result.get("total_detected_files")
    )

    if total_files == 0:
        total_files = (
            len(transferred)
            + len(missing_hospitals)
            + len(month_mismatches)
            + len(duplicates)
            + len(skipped_files)
            + len(errors)
        )

    transferred_count = len(transferred)
    missing_count = len(missing_hospitals)
    mismatch_count = len(month_mismatches)
    duplicate_count = len(duplicates)
    skipped_count = len(skipped_files)
    error_count = len(errors)

    transferred_rows = safe_int(result.get("transferred_rows_count"))

    if transferred_rows == 0:
        transferred_rows = sum(
            safe_int(
                item.get("rows")
                or item.get("transferred_rows")
                or item.get("row_count")
                or 1
            )
            for item in transferred
            if isinstance(item, dict)
        )

    processed_count = transferred_count + missing_count + mismatch_count + duplicate_count + skipped_count + error_count

    success_rate = (
        round((transferred_count / processed_count) * 100, 1)
        if processed_count
        else 0
    )

    # ========================================
    # توحيد تفاصيل جميع النتائج
    # ========================================

    detail_items = []

    def add_items(items, status, status_class, default_reason=""):
        for item in items:
            if isinstance(item, dict):
                detail_items.append({
                    "file": _text(
                        item.get("file")
                        or item.get("filename")
                        or item.get("source_file")
                    ),
                    "hospital": _text(
                        item.get("hospital")
                        or item.get("hospital_name")
                        or item.get("facility")
                    ),
                    "source_month": _text(
                        item.get("source_month")
                        or item.get("month")
                        or item.get("file_month")
                    ),
                    "master_month": _text(
                        item.get("master_month")
                        or item.get("target_month")
                    ),
                    "rows": safe_int(
                        item.get("rows")
                        or item.get("transferred_rows")
                        or item.get("row_count")
                    ),
                    "status": status,
                    "status_class": status_class,
                    "reason": _text(
                        item.get("reason")
                        or item.get("error")
                        or item.get("warning")
                        or default_reason
                    ),
                })
            else:
                detail_items.append({
                    "file": _text(item),
                    "hospital": "",
                    "source_month": "",
                    "master_month": "",
                    "rows": 0,
                    "status": status,
                    "status_class": status_class,
                    "reason": default_reason,
                })

    add_items(
        transferred,
        "تم النقل",
        "success-badge",
        "تم العثور على المستشفى والشهر ونقل البيانات بنجاح."
    )
    add_items(
        missing_hospitals,
        "المستشفى غير موجود",
        "danger-badge",
        "لم يتم العثور على المستشفى في ملف الماستر."
    )
    add_items(
        month_mismatches,
        "اختلاف الشهر",
        "warning-badge",
        "شهر الملف لا يطابق الشهر المحدد أو الموجود في الماستر."
    )
    add_items(
        duplicates,
        "تكرار",
        "duplicate-badge",
        "يوجد أكثر من سجل مطابق لنفس المستشفى والشهر."
    )
    add_items(
        skipped_files,
        "تم التجاوز",
        "muted-badge",
        "تم تجاوز الملف أو السجل."
    )
    add_items(
        errors,
        "فشل",
        "danger-badge",
        "حدث خطأ أثناء المعالجة."
    )

    detail_rows = []

    for item in detail_items:
        detail_rows.append(
            f"""
            <tr class="detail-row">
                <td class="file-name">{escape(item["file"] or "-")}</td>
                <td>{escape(item["hospital"] or "-")}</td>
                <td>{escape(item["source_month"] or "-")}</td>
                <td>{escape(item["master_month"] or "-")}</td>
                <td>{format_number(item["rows"])}</td>
                <td>
                    <span class="status-badge {item["status_class"]}">
                        {escape(item["status"])}
                    </span>
                </td>
                <td class="reason-text">{escape(item["reason"] or "-")}</td>
            </tr>
            """
        )

    if not detail_rows:
        detail_rows.append(
            """
            <tr>
                <td colspan="7" class="empty-message">
                    لا توجد نتائج مسجلة في التقرير.
                </td>
            </tr>
            """
        )

    # ========================================
    # ملخص أسباب عدم النقل
    # ========================================

    issue_summary = [
        ("المستشفى غير موجود", missing_count),
        ("اختلاف الشهر", mismatch_count),
        ("سجل مكرر", duplicate_count),
        ("تم التجاوز", skipped_count),
        ("أخطاء المعالجة", error_count),
    ]

    issue_rows = []

    for label, count in issue_summary:
        issue_rows.append(
            f"""
            <tr>
                <td>{escape(label)}</td>
                <td>{format_number(count)}</td>
            </tr>
            """
        )

    # ========================================
    # التحذيرات
    # ========================================

    warning_rows = []

    for item in warnings:
        if isinstance(item, dict):
            warning_rows.append(
                f"""
                <tr>
                    <td class="file-name">{escape(_text(item.get("file")) or "-")}</td>
                    <td>{escape(_text(item.get("hospital")) or "-")}</td>
                    <td>{escape(_text(item.get("sheet")) or "-")}</td>
                    <td>{escape(_text(item.get("warning") or item.get("reason")) or "-")}</td>
                </tr>
                """
            )
        else:
            warning_rows.append(
                f"""
                <tr>
                    <td colspan="4">{escape(_text(item))}</td>
                </tr>
                """
            )

    if not warning_rows:
        warning_rows.append(
            """
            <tr>
                <td colspan="4" class="empty-message success-message">
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
    <title>تقرير معالجة HQI | HQI Processing Report</title>

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
            --purple-700: #6a3f8f;
            --purple-100: #f0e8f7;
            --gray-700: #596670;
            --gray-100: #edf1f3;
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

        .stat-card.success {{ border-top-color: var(--green-700); }}
        .stat-card.danger {{ border-top-color: var(--red-700); }}
        .stat-card.warning {{ border-top-color: var(--amber-700); }}
        .stat-card.gold {{ border-top-color: var(--gold-600); }}
        .stat-card.purple {{ border-top-color: var(--purple-700); }}

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
            margin-top: 12px;
            color: var(--muted);
            font-size: 13px;
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
            min-width: 850px;
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

        .reason-text {{
            color: var(--muted);
        }}

        .status-badge {{
            display: inline-block;
            min-width: 92px;
            padding: 5px 10px;
            border: 1px solid transparent;
            text-align: center;
            font-size: 11px;
            font-weight: 800;
            white-space: nowrap;
        }}

        .success-badge {{ color: var(--green-700); background: var(--green-100); border-color: #cbe2d3; }}
        .danger-badge {{ color: var(--red-700); background: var(--red-100); border-color: #eccaca; }}
        .warning-badge {{ color: var(--amber-700); background: var(--amber-100); border-color: #ead8ac; }}
        .duplicate-badge {{ color: var(--purple-700); background: var(--purple-100); border-color: #d9c6e8; }}
        .muted-badge {{ color: var(--gray-700); background: var(--gray-100); border-color: #d4dce1; }}

        .empty-message {{
            padding: 28px;
            color: var(--muted);
            text-align: center;
        }}

        .success-message {{
            color: var(--green-700);
        }}

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
                        تقرير معالجة مؤشرات HQI
                        <small>HQI Processing Report</small>
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
            <section class="cards">
                <article class="stat-card">
                    <span class="stat-label-ar">إجمالي الملفات</span>
                    <span class="stat-label-en">Total Files</span>
                    <strong class="stat-value">{format_number(total_files)}</strong>
                </article>

                <article class="stat-card success">
                    <span class="stat-label-ar">تم النقل بنجاح</span>
                    <span class="stat-label-en">Successfully Transferred</span>
                    <strong class="stat-value">{format_number(transferred_count)}</strong>
                </article>

                <article class="stat-card success">
                    <span class="stat-label-ar">إجمالي الصفوف المنقولة</span>
                    <span class="stat-label-en">Transferred Rows</span>
                    <strong class="stat-value">{format_number(transferred_rows)}</strong>
                </article>

                <article class="stat-card gold">
                    <span class="stat-label-ar">نسبة نجاح النقل</span>
                    <span class="stat-label-en">Transfer Success Rate</span>
                    <strong class="stat-value">{success_rate}%</strong>
                </article>

                <article class="stat-card danger">
                    <span class="stat-label-ar">المستشفى غير موجود</span>
                    <span class="stat-label-en">Hospital Not Found</span>
                    <strong class="stat-value">{format_number(missing_count)}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">اختلاف الشهر</span>
                    <span class="stat-label-en">Month Mismatch</span>
                    <strong class="stat-value">{format_number(mismatch_count)}</strong>
                </article>

                <article class="stat-card purple">
                    <span class="stat-label-ar">السجلات المكررة</span>
                    <span class="stat-label-en">Duplicate Records</span>
                    <strong class="stat-value">{format_number(duplicate_count)}</strong>
                </article>

                <article class="stat-card warning">
                    <span class="stat-label-ar">تم التجاوز</span>
                    <span class="stat-label-en">Skipped Files</span>
                    <strong class="stat-value">{format_number(skipped_count)}</strong>
                </article>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            مؤشر الأداء العام
                            <small>Overall Transfer Performance</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body performance-grid">
                    <div>
                        <div class="progress-shell">
                            <div class="progress-value" style="width: {success_rate}%"></div>
                        </div>
                        <div class="progress-caption">
                            تم نقل <strong>{transferred_count}</strong> من أصل
                            <strong>{processed_count}</strong> نتيجة معالجة.
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
                            ملخص أسباب عدم النقل
                            <small>Transfer Issues Summary</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>السبب<small>Reason</small></th>
                                <th>العدد<small>Count</small></th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(issue_rows)}
                        </tbody>
                    </table>
                </div>
            </section>

            <section class="section">
                <div class="section-head">
                    <h2 class="section-title">
                        <span>
                            تفاصيل معالجة الملفات
                            <small>File Processing Details</small>
                        </span>
                    </h2>
                </div>

                <div class="section-body">
                    <div class="toolbar">
                        <input
                            id="detailSearch"
                            class="search-input"
                            type="text"
                            placeholder="ابحث باسم الملف أو المستشفى أو الحالة"
                            onkeyup="filterDetailTable()"
                        >

                        <div class="count-label">
                            عدد النتائج:
                            <strong>{format_number(len(detail_items))}</strong>
                        </div>
                    </div>

                    <div class="table-wrapper">
                        <table id="detailTable">
                            <thead>
                                <tr>
                                    <th>اسم الملف<small>File Name</small></th>
                                    <th>المستشفى<small>Hospital</small></th>
                                    <th>شهر المصدر<small>Source Month</small></th>
                                    <th>شهر الماستر<small>Master Month</small></th>
                                    <th>الصفوف المنقولة<small>Transferred Rows</small></th>
                                    <th>الحالة<small>Status</small></th>
                                    <th>السبب أو الملاحظة<small>Reason / Note</small></th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(detail_rows)}
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
                                        <th>المستشفى<small>Hospital</small></th>
                                        <th>ورقة العمل<small>Worksheet</small></th>
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
                <span>تم إنشاء هذا التقرير آليًا بواسطة نظام معالجة مؤشرات HQI.</span>
                <small>This report was generated automatically by the HQI Processing System.</small>
            </div>
            <div class="confidential">للاستخدام الداخلي | INTERNAL USE</div>
        </footer>
    </div>

    <script>
        function filterDetailTable() {{
            const input = document
                .getElementById("detailSearch")
                .value
                .toLowerCase();

            const rows = document.querySelectorAll(
                "#detailTable tbody .detail-row"
            );

            rows.forEach(function(row) {{
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(input) ? "" : "none";
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
