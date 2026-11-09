#!/usr/bin/env python3
"""
Calculate economic benefits from avoided deaths using country-specific VSL values.

Joins deposition and dust deaths avoided with Value of Statistical Life (VSL) data
and calculates the economic benefit for each country.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict


def read_csv_to_dict(filename):
    """Read CSV file and return dict mapping FID to row data."""
    data = {}
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('FID') or row['FID'].strip() == '':
                continue
            fid = int(row['FID'])
            data[fid] = row
    return data


def main():
    # File paths
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "test_config_output"

    dep_deaths_file = output_dir / "dep_deaths_avoided.csv"
    dust_deaths_file = output_dir / "dust_deaths_avoided.csv"
    vsl_file = output_dir / "vsl_with_fid_final.csv"
    output_file = output_dir / "economic_benefits.csv"

    print("Reading input files...")
    print(f"  - {dep_deaths_file}")
    print(f"  - {dust_deaths_file}")
    print(f"  - {vsl_file}")

    # Read CSVs into dictionaries keyed by FID
    dep_deaths = read_csv_to_dict(dep_deaths_file)
    dust_deaths = read_csv_to_dict(dust_deaths_file)
    vsl_data = read_csv_to_dict(vsl_file)

    print(f"  Loaded {len(dep_deaths)} dep deaths records")
    print(f"  Loaded {len(dust_deaths)} dust deaths records")
    print(f"  Loaded {len(vsl_data)} VSL records")

    # Calculate global average VSL
    vsl_values = [float(row['vsl']) for row in vsl_data.values()]
    global_avg_vsl = sum(vsl_values) / len(vsl_values)

    print(f"\nVSL Statistics:")
    print(f"  - Global average VSL: ${global_avg_vsl:,.2f}")

    # Build results
    results = []
    total_dep_deaths = 0
    total_dust_deaths = 0
    total_dep_benefit = 0
    total_dust_benefit = 0
    num_with_vsl = 0
    num_without_vsl = 0

    # Use dep_deaths as the base (it should have all countries)
    for fid in sorted(dep_deaths.keys()):
        dep_row = dep_deaths[fid]
        dust_row = dust_deaths.get(fid, {})
        vsl_row = vsl_data.get(fid)

        country = dep_row.get('Country', '').strip('"')
        dep_deaths_val = float(dep_row.get('Deaths', 0))
        dust_deaths_val = float(dust_row.get('Deaths', 0)) if dust_row else 0

        # Get VSL (use country-specific if available, otherwise global average)
        if vsl_row:
            vsl = float(vsl_row['vsl'])
            vsl_source = 'country'
            num_with_vsl += 1
        else:
            vsl = global_avg_vsl
            vsl_source = 'global_avg'
            num_without_vsl += 1

        # Calculate benefits
        dep_benefit = dep_deaths_val * vsl
        dust_benefit = dust_deaths_val * vsl

        # Accumulate totals
        total_dep_deaths += dep_deaths_val
        total_dust_deaths += dust_deaths_val
        total_dep_benefit += dep_benefit
        total_dust_benefit += dust_benefit

        results.append({
            'FID': fid,
            'Country': country,
            'Dep_Deaths': dep_deaths_val,
            'Dust_Deaths': dust_deaths_val,
            'VSL': vsl,
            'VSL_Source': vsl_source,
            'Dep_Benefit_USD': dep_benefit,
            'Dust_Benefit_USD': dust_benefit
        })

    print(f"  - Countries with VSL data: {num_with_vsl}")
    print(f"  - Countries using global average VSL: {num_without_vsl}")

    # Write output CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['FID', 'Country', 'Dep_Deaths', 'Dust_Deaths', 'VSL', 'VSL_Source', 'Dep_Benefit_USD', 'Dust_Benefit_USD']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nOutput saved to: {output_file}")
    print(f"\nSummary statistics:")
    print(f"  Total countries: {len(results)}")
    print(f"  Total dep deaths avoided: {total_dep_deaths:,.2f}")
    print(f"  Total dust deaths avoided: {total_dust_deaths:,.2f}")
    print(f"  Total dep benefit: ${total_dep_benefit:,.2f}")
    print(f"  Total dust benefit: ${total_dust_benefit:,.2f}")

    # Show top 10 countries by total benefit
    results_sorted = sorted(results, key=lambda x: x['Dep_Benefit_USD'] + x['Dust_Benefit_USD'], reverse=True)
    print(f"\nTop 10 countries by total economic benefit:")
    for row in results_sorted[:10]:
        total_benefit = row['Dep_Benefit_USD'] + row['Dust_Benefit_USD']
        total_deaths = row['Dep_Deaths'] + row['Dust_Deaths']
        print(f"  {row['Country']:30s} ${total_benefit:15,.0f} ({total_deaths:6.1f} deaths)")


if __name__ == "__main__":
    main()
