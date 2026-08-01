from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path


STYLE = r"""        :root {
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
        }

        * {
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
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
        }

        button,
        input {
            font: inherit;
        }

        .page-shell {
            width: min(1500px, calc(100% - 36px));
            margin: 28px auto 38px;
        }

        .official-header {
            overflow: hidden;
            color: #ffffff;
            background:
                linear-gradient(115deg, var(--navy-950) 0%, var(--navy-900) 52%, var(--teal-700) 100%);
            border: 1px solid rgba(195, 161, 93, 0.42);
            border-radius: 4px;
            box-shadow: var(--shadow);
        }

        .gold-line {
            height: 5px;
            background: linear-gradient(90deg, var(--gold-600), #e1c98c, var(--gold-600));
        }

        .header-main {
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 24px;
            padding: 24px 30px;
        }

        .identity-mark {
            width: 78px;
            height: 78px;
            display: grid;
            place-items: center;
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.07);
            box-shadow: inset 0 0 0 5px rgba(195, 161, 93, 0.10);
        }

        .identity-mark svg {
            width: 52px;
            height: 52px;
            fill: none;
            stroke: #e5ce93;
            stroke-width: 1.5;
            stroke-linecap: round;
            stroke-linejoin: round;
        }

        .identity-copy {
            min-width: 0;
        }

        .authority-ar {
            display: block;
            margin-bottom: 3px;
            color: #ffffff;
            font-size: 20px;
            font-weight: 800;
        }

        .authority-en {
            display: block;
            color: rgba(255, 255, 255, 0.76);
            font-size: 12px;
            letter-spacing: 1.1px;
            text-transform: uppercase;
            direction: ltr;
            text-align: right;
        }

        .document-class {
            min-width: 190px;
            padding: 12px 16px;
            border-right: 3px solid var(--gold-500);
            background: rgba(0, 0, 0, 0.13);
        }

        .document-class span {
            display: block;
            color: rgba(255, 255, 255, 0.66);
            font-size: 11px;
        }

        .document-class strong {
            display: block;
            margin-top: 2px;
            color: #ffffff;
            font-size: 14px;
        }

        .report-hero {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 24px;
            align-items: end;
            padding: 28px 30px 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(0, 0, 0, 0.10);
        }

        .report-title .overline {
            display: block;
            margin-bottom: 8px;
            color: #e4cd94;
            font-size: 12px;
            font-weight: 700;
        }

        .report-title h1 {
            margin: 0;
            color: #ffffff;
            font-size: clamp(28px, 4vw, 44px);
            line-height: 1.22;
        }

        .report-title h1 small {
            display: block;
            margin-top: 8px;
            color: rgba(255, 255, 255, 0.70);
            font-size: 15px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }

        .report-meta {
            display: grid;
            grid-template-columns: repeat(3, minmax(150px, 1fr));
            gap: 1px;
            background: rgba(255, 255, 255, 0.17);
            border: 1px solid rgba(255, 255, 255, 0.17);
        }

        .meta-item {
            min-height: 78px;
            padding: 13px 16px;
            background: rgba(7, 27, 42, 0.72);
        }

        .meta-item span {
            display: block;
            color: rgba(255, 255, 255, 0.58);
            font-size: 10px;
            line-height: 1.35;
        }

        .meta-item strong {
            display: block;
            margin-top: 7px;
            color: #ffffff;
            font-size: 13px;
            overflow-wrap: anywhere;
        }

        .content {
            margin-top: 22px;
        }

        .section {
            margin-bottom: 20px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 4px;
            box-shadow: 0 8px 24px rgba(7, 27, 42, 0.055);
        }

        .section-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 17px 20px;
            border-bottom: 1px solid var(--line);
            background: linear-gradient(180deg, #ffffff, #f7f9fa);
        }

        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
            color: var(--navy-900);
            font-size: 18px;
        }

        .section-title::before {
            content: "";
            width: 4px;
            height: 30px;
            background: linear-gradient(var(--gold-500), var(--gold-600));
        }

        .section-title small {
            display: block;
            margin-top: 1px;
            color: var(--muted);
            font-size: 11px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }

        .section-body {
            padding: 20px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }

        .stat-card {
            position: relative;
            min-height: 140px;
            padding: 19px;
            overflow: hidden;
            background: #ffffff;
            border: 1px solid var(--line);
            border-top: 4px solid var(--navy-700);
            box-shadow: 0 6px 18px rgba(7, 27, 42, 0.05);
        }

        .stat-card.success { border-top-color: var(--green-700); }
        .stat-card.danger { border-top-color: var(--red-700); }
        .stat-card.warning { border-top-color: var(--amber-700); }
        .stat-card.gold { border-top-color: var(--gold-600); }
        .stat-card.purple { border-top-color: var(--purple-700); }

        .stat-label-ar {
            display: block;
            color: var(--navy-900);
            font-size: 13px;
            font-weight: 750;
        }

        .stat-label-en {
            display: block;
            margin-top: 1px;
            color: var(--muted);
            font-size: 10px;
            direction: ltr;
            text-align: right;
        }

        .stat-value {
            display: block;
            margin-top: 16px;
            color: var(--ink);
            font-size: 32px;
            font-weight: 800;
            line-height: 1;
            direction: ltr;
            text-align: right;
        }

        .performance-grid {
            display: grid;
            grid-template-columns: 1.4fr 0.6fr;
            gap: 20px;
            align-items: center;
        }

        .progress-shell {
            height: 22px;
            overflow: hidden;
            background: #e4e9ec;
            border: 1px solid #d5dde2;
        }

        .progress-value {
            height: 100%;
            background: linear-gradient(90deg, var(--teal-700), var(--teal-600));
        }

        .progress-caption {
            margin-top: 12px;
            color: var(--muted);
            font-size: 13px;
        }

        .performance-score {
            padding: 18px;
            text-align: center;
            background: var(--navy-900);
            border-bottom: 4px solid var(--gold-500);
        }

        .performance-score span {
            display: block;
            color: rgba(255, 255, 255, 0.66);
            font-size: 11px;
        }

        .performance-score strong {
            display: block;
            margin: 4px 0;
            color: #ffffff;
            font-size: 38px;
            line-height: 1.1;
            direction: ltr;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        table {
            width: 100%;
            min-width: 850px;
            border-collapse: collapse;
        }

        th {
            padding: 13px 12px;
            color: #ffffff;
            background: var(--navy-800);
            border-left: 1px solid rgba(255, 255, 255, 0.10);
            font-size: 12px;
            text-align: right;
            vertical-align: bottom;
        }

        th small {
            display: block;
            margin-top: 2px;
            color: rgba(255, 255, 255, 0.62);
            font-size: 9px;
            font-weight: 500;
            direction: ltr;
            text-align: right;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #e3e8eb;
            border-left: 1px solid #edf0f2;
            font-size: 13px;
            vertical-align: middle;
        }

        tbody tr:nth-child(even) {
            background: #f8fafb;
        }

        tbody tr:hover {
            background: #eef5f4;
        }

        .file-name {
            direction: ltr;
            text-align: left;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12px;
        }

        .reason-text {
            color: var(--muted);
        }

        .status-badge {
            display: inline-block;
            min-width: 92px;
            padding: 5px 10px;
            border: 1px solid transparent;
            text-align: center;
            font-size: 11px;
            font-weight: 800;
            white-space: nowrap;
        }

        .success-badge { color: var(--green-700); background: var(--green-100); border-color: #cbe2d3; }
        .danger-badge { color: var(--red-700); background: var(--red-100); border-color: #eccaca; }
        .warning-badge { color: var(--amber-700); background: var(--amber-100); border-color: #ead8ac; }
        .duplicate-badge { color: var(--purple-700); background: var(--purple-100); border-color: #d9c6e8; }
        .muted-badge { color: var(--gray-700); background: var(--gray-100); border-color: #d4dce1; }

        .empty-message {
            padding: 28px;
            color: var(--muted);
            text-align: center;
        }

        .success-message {
            color: var(--green-700);
        }

        .toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 16px;
        }

        .search-input {
            width: min(430px, 100%);
            padding: 11px 13px;
            color: var(--ink);
            background: #ffffff;
            border: 1px solid #bdc8cf;
            border-radius: 2px;
            outline: none;
        }

        .search-input:focus {
            border-color: var(--teal-700);
            box-shadow: 0 0 0 3px rgba(15, 98, 95, 0.10);
        }

        .count-label {
            padding: 9px 13px;
            color: var(--navy-900);
            background: var(--sand-100);
            border-right: 3px solid var(--gold-600);
            font-size: 12px;
        }

        details {
            border: 1px solid var(--line);
        }

        summary {
            cursor: pointer;
            padding: 15px 17px;
            color: var(--navy-900);
            background: #f5f7f8;
            font-weight: 750;
        }

        details[open] summary {
            border-bottom: 1px solid var(--line);
        }

        details .table-wrapper {
            padding: 12px;
        }

        .report-footer {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 20px;
            align-items: center;
            padding: 18px 22px;
            color: #ffffff;
            background: var(--navy-950);
            border-top: 4px solid var(--gold-600);
            font-size: 11px;
        }

        .report-footer small {
            display: block;
            color: rgba(255, 255, 255, 0.56);
            direction: ltr;
            text-align: right;
        }

        .confidential {
            padding: 7px 10px;
            color: #e5ce93;
            border: 1px solid rgba(229, 206, 147, 0.48);
            letter-spacing: 0.8px;
            white-space: nowrap;
        }

        @media (max-width: 1100px) {
            .header-main {
                grid-template-columns: auto 1fr;
            }

            .document-class {
                grid-column: 1 / -1;
            }

            .report-hero {
                grid-template-columns: 1fr;
            }

            .report-meta {
                grid-template-columns: repeat(3, 1fr);
            }

            .cards {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 720px) {
            .page-shell {
                width: min(100% - 18px, 1500px);
                margin-top: 9px;
            }

            .header-main {
                grid-template-columns: 1fr;
                text-align: center;
            }

            .identity-mark {
                margin: 0 auto;
            }

            .authority-en {
                text-align: center;
            }

            .document-class {
                border-right: 0;
                border-top: 3px solid var(--gold-500);
            }

            .report-hero {
                padding: 22px 18px;
            }

            .report-meta {
                grid-template-columns: 1fr;
            }

            .cards {
                grid-template-columns: 1fr;
            }

            .performance-grid {
                grid-template-columns: 1fr;
            }

            .section-head,
            .toolbar {
                align-items: stretch;
                flex-direction: column;
            }

            .section-body {
                padding: 13px;
            }

            .report-footer {
                grid-template-columns: 1fr;
                text-align: center;
            }

            .report-footer small {
                text-align: center;
            }
        }

        @media print {
            @page {
                size: A4 landscape;
                margin: 10mm;
            }

            body {
                background: #ffffff;
            }

            .page-shell {
                width: 100%;
                margin: 0;
            }

            .official-header,
            .section,
            .stat-card {
                box-shadow: none;
            }

            .search-input {
                display: none;
            }

            .section,
            .stat-card {
                break-inside: avoid;
            }
        }"""


def _as_list(value):
    return value if isinstance(value, list) else []


def _text(value) -> str:
    return str(value or "").strip()


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _format_number(value) -> str:
    return f"{_safe_int(value):,}"


def create_adaa_report(result, report_path):
    """إنشاء تقرير HTML احترافي لنتائج معالجة ADAA الأسبوعية."""
    report_path = Path(report_path)
    output_file = Path(
        result.get("output_file")
        or result.get("output_path")
        or "ADAA_Weekly_Output.xlsx"
    )

    processed = _as_list(result.get("processed"))
    errors = _as_list(result.get("errors"))
    processed_count = _safe_int(result.get("processed_count", len(processed)))
    error_count = _safe_int(result.get("error_count", len(errors)))
    total_files = processed_count + error_count
    success_rate = round((processed_count / total_files) * 100, 1) if total_files else 0

    type_counts = Counter(
        _text(item.get("type")).upper()
        for item in processed
        if isinstance(item, dict) and _text(item.get("type"))
    )

    detail_rows = []
    for item in processed:
        if not isinstance(item, dict):
            continue
        detail_rows.append(
            "<tr class='detail-row'>"
            f"<td class='file-name'>{escape(_text(item.get('file')) or '-')}</td>"
            f"<td>{escape(_text(item.get('type')) or '-')}</td>"
            f"<td>{escape(_text(item.get('facility_code')) or '-')}</td>"
            f"<td>{escape(_text(item.get('week')) or '-')}</td>"
            f"<td>{escape(_text(item.get('target_sheet')) or '-')}</td>"
            f"<td>{escape(_text(item.get('target_row')) or '-')}</td>"
            "<td><span class='status-badge success-badge'>تم النقل</span></td>"
            "<td class='reason-text'>تمت مطابقة المنشأة والأسبوع ونقل البيانات بنجاح.</td>"
            "</tr>"
        )

    error_rows = []
    for item in errors:
        if isinstance(item, dict):
            file_name = _text(item.get("file"))
            reason = _text(item.get("error") or item.get("reason"))
        else:
            file_name = _text(item)
            reason = "حدث خطأ أثناء المعالجة."

        detail_rows.append(
            "<tr class='detail-row'>"
            f"<td class='file-name'>{escape(file_name or '-')}</td>"
            "<td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>"
            "<td><span class='status-badge danger-badge'>فشل</span></td>"
            f"<td class='reason-text'>{escape(reason or '-')}</td>"
            "</tr>"
        )
        error_rows.append(
            "<tr>"
            f"<td class='file-name'>{escape(file_name or '-')}</td>"
            f"<td>{escape(reason or '-')}</td>"
            "</tr>"
        )

    if not detail_rows:
        detail_rows.append("<tr><td colspan='8' class='empty-message'>لا توجد نتائج مسجلة.</td></tr>")
    if not error_rows:
        error_rows.append("<tr><td colspan='2' class='empty-message success-message'>لا توجد أخطاء.</td></tr>")

    replacements = {
        "__OUTPUT_FILE__": escape(output_file.name),
        "__GENERATED_AT__": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "__TOTAL__": _format_number(total_files),
        "__PROCESSED__": _format_number(processed_count),
        "__ERRORS__": _format_number(error_count),
        "__SUCCESS_RATE__": str(success_rate),
        "__LB_COUNT__": _format_number(type_counts.get("LB", 0)),
        "__BB_COUNT__": _format_number(type_counts.get("BB", 0)),
        "__OR_COUNT__": _format_number(type_counts.get("OR", 0)),
        "__DETAIL_ROWS__": "".join(detail_rows),
        "__ERROR_ROWS__": "".join(error_rows),
    }

    html_content = HTML_TEMPLATE.replace("__STYLE__", STYLE)
    for key, value in replacements.items():
        html_content = html_content.replace(key, value)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html_content, encoding="utf-8")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تقرير معالجة ADAA | ADAA Processing Report</title>
<style>
__STYLE__
.type-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.type-box{padding:18px;background:#fff;border:1px solid var(--line);border-right:4px solid var(--teal-700)}
.type-box span{display:block;color:var(--muted);font-size:12px}
.type-box strong{display:block;margin-top:7px;color:var(--navy-900);font-size:28px;direction:ltr;text-align:right}
@media(max-width:720px){.type-summary{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="page-shell">
<header class="official-header">
<div class="gold-line"></div>
<div class="header-main">
<div class="identity-mark" aria-hidden="true">
<svg viewBox="0 0 64 64"><path d="M32 6l18 8v14c0 13-7.7 23.5-18 29-10.3-5.5-18-16-18-29V14z"></path><path d="M32 18v26M19 31h26"></path><path d="M26 13h12M26 49h12"></path></svg>
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
<span class="overline">إدارة الاستراتيجية والأداء | Strategy & Performance Department</span>
<h1>تقرير معالجة مؤشرات ADAA الأسبوعية<small>ADAA Weekly Processing Report</small></h1>
</div>
<div class="report-meta">
<div class="meta-item"><span>الملف الناتج<br>Output File</span><strong>__OUTPUT_FILE__</strong></div>
<div class="meta-item"><span>نوع المعالجة<br>Processing Type</span><strong>أسبوعي | Weekly</strong></div>
<div class="meta-item"><span>تاريخ الإصدار<br>Issue Date</span><strong>__GENERATED_AT__</strong></div>
</div>
</div>
</header>

<main class="content">
<section class="cards">
<article class="stat-card"><span class="stat-label-ar">إجمالي الملفات</span><span class="stat-label-en">Total Files</span><strong class="stat-value">__TOTAL__</strong></article>
<article class="stat-card success"><span class="stat-label-ar">تمت المعالجة بنجاح</span><span class="stat-label-en">Successfully Processed</span><strong class="stat-value">__PROCESSED__</strong></article>
<article class="stat-card danger"><span class="stat-label-ar">ملفات فشلت</span><span class="stat-label-en">Failed Files</span><strong class="stat-value">__ERRORS__</strong></article>
<article class="stat-card gold"><span class="stat-label-ar">نسبة النجاح</span><span class="stat-label-en">Success Rate</span><strong class="stat-value">__SUCCESS_RATE__%</strong></article>
</section>

<section class="section">
<div class="section-head"><h2 class="section-title"><span>توزيع الملفات حسب البرنامج<small>Files by ADAA Program</small></span></h2></div>
<div class="section-body type-summary">
<div class="type-box"><span>المختبر | Laboratory (LB)</span><strong>__LB_COUNT__</strong></div>
<div class="type-box"><span>بنك الدم | Blood Bank (BB)</span><strong>__BB_COUNT__</strong></div>
<div class="type-box"><span>غرف العمليات | Operating Room (OR)</span><strong>__OR_COUNT__</strong></div>
</div>
</section>

<section class="section">
<div class="section-head"><h2 class="section-title"><span>مؤشر الأداء العام<small>Overall Processing Performance</small></span></h2></div>
<div class="section-body performance-grid">
<div>
<div class="progress-shell"><div class="progress-value" style="width:__SUCCESS_RATE__%"></div></div>
<div class="progress-caption">تمت معالجة <strong>__PROCESSED__</strong> من أصل <strong>__TOTAL__</strong> ملف.</div>
</div>
<div class="performance-score"><span>نسبة النجاح | Success Rate</span><strong>__SUCCESS_RATE__%</strong><span>النتيجة التشغيلية | Operational Result</span></div>
</div>
</section>

<section class="section">
<div class="section-head"><h2 class="section-title"><span>تفاصيل معالجة الملفات<small>File Processing Details</small></span></h2></div>
<div class="section-body">
<div class="toolbar">
<input id="detailSearch" class="search-input" type="text" placeholder="ابحث باسم الملف أو المنشأة أو النوع أو الحالة" onkeyup="filterDetailTable()">
<div class="count-label">عدد النتائج: <strong>__TOTAL__</strong></div>
</div>
<div class="table-wrapper">
<table id="detailTable">
<thead><tr>
<th>اسم الملف<small>File Name</small></th>
<th>البرنامج<small>Program</small></th>
<th>رمز المنشأة<small>Facility Code</small></th>
<th>الأسبوع<small>Week</small></th>
<th>شيت الماستر<small>Master Sheet</small></th>
<th>صف الوجهة<small>Target Row</small></th>
<th>الحالة<small>Status</small></th>
<th>الملاحظة<small>Note</small></th>
</tr></thead>
<tbody>__DETAIL_ROWS__</tbody>
</table>
</div>
</div>
</section>

<section class="section">
<div class="section-body">
<details>
<summary>عرض تفاصيل الأخطاء | View Error Details (__ERRORS__)</summary>
<div class="table-wrapper">
<table>
<thead><tr><th>اسم الملف<small>File Name</small></th><th>سبب الخطأ<small>Error Reason</small></th></tr></thead>
<tbody>__ERROR_ROWS__</tbody>
</table>
</div>
</details>
</div>
</section>
</main>

<footer class="report-footer">
<div><span>تم إنشاء هذا التقرير آليًا بواسطة نظام معالجة مؤشرات ADAA.</span><small>This report was generated automatically by the ADAA Processing System.</small></div>
<div class="confidential">للاستخدام الداخلي | INTERNAL USE</div>
</footer>
</div>

<script>
function filterDetailTable(){
const input=document.getElementById("detailSearch").value.toLowerCase();
const rows=document.querySelectorAll("#detailTable tbody .detail-row");
rows.forEach(function(row){row.style.display=row.innerText.toLowerCase().includes(input)?"":"none";});
}
</script>
</body>
</html>
"""
