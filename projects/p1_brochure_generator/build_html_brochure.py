"""
Script to build a professional, Tailwind CSS v3 based Enterprise Brochure HTML
from a generated brochure JSON file.
"""

import json
from pathlib import Path
import html

def generate_brochure_html(json_path: Path, output_html_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    company = data.get("company", {})
    target_audience = data.get("target_audience", {})
    offerings = data.get("offerings", [])
    key_differentiators = data.get("key_differentiators", [])
    pricing = data.get("pricing", [])
    contact = data.get("contact_and_cta", {})
    verdict = data.get("summary_verdict", "")

    # Group offerings by category
    categories = sorted(list(set(o.get("category", "General") for o in offerings)))

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(company.get('name', 'Enterprise'))} — Executive Business Brochure</title>
  
  <!-- Google Fonts: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Tailwind CSS v3 Play CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
          }},
          colors: {{
            brand: {{
              50: '#eef2ff',
              100: '#e0e7ff',
              200: '#c7d2fe',
              300: '#a5b4fc',
              400: '#818cf8',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
              800: '#3730a3',
              900: '#312e81',
              950: '#1e1b4b',
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    @media print {{
      .no-print {{ display: none !important; }}
      body {{ background: white !important; color: black !important; }}
      .page-break {{ page-break-before: always; }}
    }}
    .glass-nav {{
      background: rgba(255, 255, 255, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }}
    .dark .glass-nav {{
      background: rgba(15, 23, 42, 0.85);
    }}
  </style>
</head>

<body class="bg-slate-50 text-slate-900 antialiased selection:bg-brand-500 selection:text-white">

  <!-- Top Announcement Bar / Breadcrumb -->
  <div class="bg-slate-900 text-slate-300 text-xs py-2 px-4 text-center font-medium tracking-wide no-print flex justify-between items-center max-w-7xl mx-auto rounded-b-xl">
    <div class="flex items-center space-x-2">
      <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      <span>Enterprise Intelligence Brochure &bull; Generated via AI Agentic Engine</span>
    </div>
    <div class="flex items-center space-x-3">
      <button onclick="window.print()" class="hover:text-white flex items-center gap-1 font-semibold text-brand-300 transition-colors">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
        Print / PDF
      </button>
    </div>
  </div>

  <!-- Sticky Header Navigation -->
  <header class="sticky top-0 z-50 glass-nav border-b border-slate-200/80 transition-all duration-200 no-print">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white font-bold text-xl shadow-md shadow-brand-500/20">
          {company.get('name', 'S')[0]}
        </div>
        <div>
          <span class="font-extrabold text-xl tracking-tight text-slate-900">{html.escape(company.get('name', 'Enterprise'))}</span>
          <span class="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">Executive Brochure</span>
        </div>
      </div>
      <nav class="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
        <a href="#overview" class="hover:text-brand-600 transition-colors">Overview</a>
        <a href="#differentiators" class="hover:text-brand-600 transition-colors">Differentiators</a>
        <a href="#solutions" class="hover:text-brand-600 transition-colors">Offerings ({len(offerings)})</a>
        <a href="#audience" class="hover:text-brand-600 transition-colors">Audience</a>
        <a href="#pricing" class="hover:text-brand-600 transition-colors">Pricing</a>
      </nav>
      <div>
        <a href="{html.escape(contact.get('demo_or_signup_url') or 'https://stripe.com')}" target="_blank" class="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm px-4 py-2 rounded-lg shadow-sm hover:shadow transition-all">
          <span>{html.escape(contact.get('primary_cta', 'Get Started')[:22])}</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </a>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section id="overview" class="relative overflow-hidden pt-12 pb-16 lg:pt-20 lg:pb-24 border-b border-slate-200 bg-white">
    <div class="absolute inset-0 bg-gradient-to-b from-brand-50/50 via-white to-white pointer-events-none"></div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      <div class="max-w-3xl">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-100 text-brand-800 text-xs font-semibold mb-6">
          <span class="w-1.5 h-1.5 rounded-full bg-brand-600"></span>
          Enterprise Architecture Brief
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-950 tracking-tight leading-[1.1] mb-6">
          {html.escape(company.get('tagline', 'Financial infrastructure to grow your revenue.'))}
        </h1>
        <p class="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal mb-8">
          {html.escape(company.get('mission_statement', ''))}
        </p>
        
        <div class="flex flex-wrap items-center gap-4">
          <a href="{html.escape(contact.get('demo_or_signup_url') or '#')}" target="_blank" class="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-base px-6 py-3 rounded-xl shadow-lg shadow-slate-900/10 transition-all flex items-center gap-2">
            <span>Explore Platform</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          </a>
          <a href="#solutions" class="bg-white hover:bg-slate-50 text-slate-700 font-semibold text-base px-6 py-3 rounded-xl border border-slate-300 transition-all">
            View All Capabilities ({len(offerings)})
          </a>
        </div>
      </div>

      <!-- Quick Metrics Strip -->
      <div class="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 pt-10 border-t border-slate-200">
        <div class="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/70">
          <div class="text-2xl sm:text-3xl font-extrabold text-brand-600 mb-1">$1.9 Trillion</div>
          <div class="text-xs sm:text-sm text-slate-600 font-medium">Payment Volume Processed (2025)</div>
        </div>
        <div class="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/70">
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-1">99.999%</div>
          <div class="text-xs sm:text-sm text-slate-600 font-medium">Historical Platform Uptime</div>
        </div>
        <div class="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/70">
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-1">135+ / 125+</div>
          <div class="text-xs sm:text-sm text-slate-600 font-medium">Currencies & Payment Methods</div>
        </div>
        <div class="bg-slate-50/80 p-5 rounded-2xl border border-slate-200/70">
          <div class="text-2xl sm:text-3xl font-extrabold text-brand-600 mb-1">5 Million+</div>
          <div class="text-xs sm:text-sm text-slate-600 font-medium">Active Businesses Built on Platform</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Executive Market Verdict -->
  <section class="py-12 bg-gradient-to-r from-brand-900 to-indigo-950 text-white relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0 text-brand-300">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
        </div>
        <div>
          <h2 class="text-xs uppercase tracking-widest text-brand-300 font-semibold mb-2">Executive Market Verdict</h2>
          <p class="text-base sm:text-lg text-slate-200 leading-relaxed font-light">
            {html.escape(verdict)}
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- Key Differentiators Grid -->
  <section id="differentiators" class="py-16 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center max-w-2xl mx-auto mb-14">
      <span class="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full">Competitive Edge</span>
      <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight mt-3">Why Industry Leaders Choose This Platform</h2>
      <p class="text-slate-600 mt-3 text-sm sm:text-base">Key strategic capabilities that distinguish this enterprise infrastructure from alternatives.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
"""

    for i, diff in enumerate(key_differentiators):
        html_content += f"""
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
        <div>
          <div class="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-sm mb-4">
            0{i+1}
          </div>
          <h3 class="font-bold text-slate-900 text-base mb-3 leading-snug">
            {html.escape(diff.get('differentiator', ''))}
          </h3>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-100 bg-slate-50/60 -mx-6 -mb-6 p-4 rounded-b-2xl">
          <div class="text-xs font-semibold text-brand-700 uppercase tracking-wider mb-1">Measurable Business Impact</div>
          <p class="text-xs text-slate-700 leading-relaxed">{html.escape(diff.get('business_impact', ''))}</p>
        </div>
      </div>
"""

    html_content += f"""
    </div>
  </section>

  <!-- Target Audience & Core Pain Points -->
  <section id="audience" class="py-16 bg-slate-100/70 border-y border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        <!-- ICP & Industries -->
        <div class="lg:col-span-6 bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <div class="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-600 mb-3">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
            Ideal Customer Profile (ICP)
          </div>
          <h3 class="text-xl font-bold text-slate-900 mb-4">Who This Platform is Built For</h3>
          <p class="text-slate-600 text-sm leading-relaxed mb-6">
            {html.escape(target_audience.get('ideal_customer_profile', ''))}
          </p>

          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Target Industry Sectors</h4>
          <div class="flex flex-wrap gap-2">
"""
    for ind in target_audience.get("primary_industries", []):
        html_content += f"""            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200 hover:bg-brand-50 hover:text-brand-700 transition-colors">{html.escape(ind)}</span>\n"""

    html_content += f"""
          </div>
        </div>

        <!-- Pain Points Solved -->
        <div class="lg:col-span-6 bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
          <div class="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-600 mb-3">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            Critical Business Pain Points Solved
          </div>
          <h3 class="text-xl font-bold text-slate-900 mb-4">Obstacles Removed for Enterprises</h3>
          
          <ul class="space-y-3">
"""
    for pp in target_audience.get("core_pain_points", []):
        html_content += f"""
            <li class="flex items-start gap-3 text-sm text-slate-700">
              <span class="shrink-0 w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-xs mt-0.5">&check;</span>
              <span>{html.escape(pp)}</span>
            </li>
"""

    html_content += f"""
          </ul>
        </div>

      </div>
    </div>
  </section>

  <!-- Complete Product & Offerings Catalog with Filter Tabs -->
  <section id="solutions" class="py-16 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
      <div>
        <span class="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full">Product & Solution Matrix</span>
        <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight mt-2">Enterprise Capabilities ({len(offerings)})</h2>
        <p class="text-slate-600 text-sm mt-1">Modular and composable building blocks designed to operate seamlessly together.</p>
      </div>
      
      <!-- Category Filter Pills -->
      <div class="flex flex-wrap gap-1.5 no-print" id="category-filter">
        <button onclick="filterCategory('ALL')" class="category-btn active px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 text-white transition-all">All ({len(offerings)})</button>
"""
    for cat in categories:
        count = sum(1 for o in offerings if o.get("category") == cat)
        html_content += f"""        <button onclick="filterCategory('{html.escape(cat)}')" class="category-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all">{html.escape(cat)} ({count})</button>\n"""

    html_content += f"""
      </div>
    </div>

    <!-- Offerings Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="offerings-grid">
"""

    for off in offerings:
        cat = off.get("category", "General")
        html_content += f"""
      <div class="offering-card bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:border-brand-300 hover:shadow-md transition-all flex flex-col justify-between" data-category="{html.escape(cat)}">
        <div>
          <div class="flex items-center justify-between mb-3">
            <span class="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 text-slate-600">{html.escape(cat)}</span>
          </div>
          <h3 class="text-lg font-bold text-slate-900 mb-2">{html.escape(off.get('name', ''))}</h3>
          <p class="text-xs text-slate-600 leading-relaxed mb-4">{html.escape(off.get('description', ''))}</p>
          
          <div class="space-y-1.5 mb-4">
"""
        for feat in off.get("key_features", []):
            html_content += f"""
            <div class="flex items-start gap-2 text-xs text-slate-700">
              <span class="text-brand-600 font-bold shrink-0">&bull;</span>
              <span>{html.escape(feat)}</span>
            </div>
"""

        html_content += f"""
          </div>
        </div>

        <div class="pt-3 border-t border-slate-100 text-[11px] text-slate-500">
          <span class="font-semibold text-slate-700">Use Case:</span> {html.escape(off.get('target_use_case', 'Enterprise implementation'))}
        </div>
      </div>
"""

    html_content += f"""
    </div>
  </section>

  <!-- Pricing & Engagement Models -->
  <section id="pricing" class="py-16 bg-white border-t border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <span class="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full">Transparent Economics</span>
        <h2 class="text-3xl font-extrabold text-slate-900 tracking-tight mt-3">Pricing & Engagement Architecture</h2>
        <p class="text-slate-600 mt-2 text-sm">Flexible engagement models designed to adapt from early-stage to high-volume enterprises.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
"""

    for i, tier in enumerate(pricing):
        is_featured = i == 1
        card_border = "border-brand-500 ring-2 ring-brand-500/20 shadow-lg" if is_featured else "border-slate-200 shadow-sm"
        badge = f"""<span class="absolute -top-3 right-6 px-3 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-brand-600 text-white">Recommended</span>""" if is_featured else ""

        html_content += f"""
        <div class="relative bg-white rounded-3xl p-7 border {card_border} flex flex-col justify-between">
          {badge}
          <div>
            <h3 class="text-lg font-bold text-slate-900 mb-1">{html.escape(tier.get('tier_name', 'Plan'))}</h3>
            <div class="text-2xl font-black text-slate-950 my-3">{html.escape(tier.get('price_info', 'Custom'))}</div>
            <p class="text-xs text-slate-500 font-medium mb-6">Billing cycle: {html.escape(tier.get('billing_period') or 'Flexible / Per Usage')}</p>
            
            <ul class="space-y-3 mb-6">
"""
        for h in tier.get("highlights", []):
            html_content += f"""
              <li class="flex items-start gap-2.5 text-xs text-slate-700">
                <svg class="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                <span>{html.escape(h)}</span>
              </li>
"""
        html_content += f"""
            </ul>
          </div>

          <a href="{html.escape(contact.get('demo_or_signup_url') or '#')}" target="_blank" class="w-full text-center py-2.5 px-4 rounded-xl text-xs font-bold transition-all {'bg-brand-600 hover:bg-brand-700 text-white shadow-sm' if is_featured else 'bg-slate-100 hover:bg-slate-200 text-slate-800'}">
            Select & Explore
          </a>
        </div>
"""

    html_content += f"""
      </div>
    </div>
  </section>

  <!-- CTA Banner -->
  <section class="py-16 sm:py-20 bg-slate-950 text-white relative overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-r from-brand-900/40 via-indigo-950/30 to-slate-950 pointer-events-none"></div>
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
      <h2 class="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
        Ready to Build on {html.escape(company.get('name', 'Enterprise Infrastructure'))}?
      </h2>
      <p class="text-slate-300 text-base max-w-2xl mx-auto mb-8">
        {html.escape(contact.get('primary_cta', 'Get started today or contact our solutions team to design a custom integration for your enterprise.'))}
      </p>
      <div class="flex flex-wrap items-center justify-center gap-4">
        <a href="{html.escape(contact.get('demo_or_signup_url') or 'https://stripe.com')}" target="_blank" class="bg-brand-500 hover:bg-brand-400 text-slate-950 font-bold px-8 py-3.5 rounded-xl shadow-lg shadow-brand-500/25 transition-all text-sm">
          Get Started Now
        </a>
        <button onclick="window.print()" class="bg-white/10 hover:bg-white/15 text-white font-semibold px-6 py-3.5 rounded-xl border border-white/20 transition-all text-sm no-print">
          Download PDF / Print
        </button>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="py-8 bg-slate-900 text-slate-400 text-xs border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        &copy; 2026 {html.escape(company.get('name', 'Enterprise'))} &bull; Document compiled for executive evaluation.
      </div>
      <div class="flex items-center gap-4">
        <span>Framework: Tailwind CSS v3</span>
        <span>&bull;</span>
        <span>AI Engine: Instructor + Pydantic v2</span>
      </div>
    </div>
  </footer>

  <!-- Interactive JavaScript for Category Filtering -->
  <script>
    function filterCategory(category) {{
      const buttons = document.querySelectorAll('.category-btn');
      buttons.forEach(btn => {{
        if (btn.innerText.includes(category) || (category === 'ALL' && btn.innerText.includes('All'))) {{
          btn.className = 'category-btn active px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 text-white transition-all';
        }} else {{
          btn.className = 'category-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all';
        }}
      }});

      const cards = document.querySelectorAll('.offering-card');
      cards.forEach(card => {{
        if (category === 'ALL' || card.getAttribute('data-category') === category) {{
          card.style.display = 'flex';
        }} else {{
          card.style.display = 'none';
        }}
      }});
    }}
  </script>

</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML Brochure successfully created at: {output_html_path}")

if __name__ == "__main__":
    json_file = Path(r"E:\DockerProjects\saaa_rag_product\ai-engineering\projects\p1_brochure_generator\output\stripe_com_brochure.json")
    html_file = Path(r"E:\DockerProjects\saaa_rag_product\ai-engineering\projects\p1_brochure_generator\output\stripe_com_brochure.html")
    generate_brochure_html(json_file, html_file)
