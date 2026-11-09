#!/usr/bin/env python3
"""
Calculate dust emission difference between vegetation scenarios and convert to InMAP format.

This script:
1. Reads dust emissions from vegetated and devegetated scenarios (GeoTIFF format)
2. Calculates the difference (vegetation_off - vegetation_on)
3. Converts to InMAP-compatible NetCDF format with requirements:
   - NETCDF-3 64-bit offset format (supports large files >2GB, InMAP compatible)
   - Latitude coordinates in ascending order (south to north: -90 to +90)
   - Variable name "PM2_5"
   - All NaN/missing values replaced with 0
   - CF-compliant coordinate attributes (units, standard_name) for QGIS compatibility

Usage:
    python utils/calculate_dust_difference_inmap.py <vegetation_on_file> <vegetation_off_file> <output_file>

Example:
    python utils/calculate_dust_difference_inmap.py \\
        vegetation_on/2019_dust_vegetation_on.tiff \\
        vegetation_off/2019_dust_vegetation_off.tiff \\
        outputs/dust_difference_2019_inmap.nc
"""

import sys
import rasterio
import xarray as xr
import numpy as np


def calculate_dust_difference_inmap(veg_on_file, veg_off_file, output_file):
    """
    Calculate dust emission difference and save in InMAP-compatible format.

    Parameters:
    -----------
    veg_on_file : str
        Path to vegetation ON dust emissions (GeoTIFF)
    veg_off_file : str
        Path to vegetation OFF dust emissions (GeoTIFF)
    output_file : str
        Path to output NetCDF file (InMAP-compatible format)
    """
    print("="*80)
    print("DUST EMISSION DIFFERENCE CALCULATION FOR INMAP")
    print("="*80)

    print(f"\nLoading vegetation ON dust emissions: {veg_on_file}")
    with rasterio.open(veg_on_file) as src:
        veg_on_data = src.read(1)
        transform = src.transform
        crs = src.crs
        width = src.width
        height = src.height

        print(f"  Shape: {veg_on_data.shape}")
        print(f"  Total emissions: {np.nansum(veg_on_data):,.0f} kg")
        print(f"  CRS: {crs}")

    print(f"\nLoading vegetation OFF dust emissions: {veg_off_file}")
    with rasterio.open(veg_off_file) as src:
        veg_off_data = src.read(1)

        # Verify dimensions match
        if veg_off_data.shape != veg_on_data.shape:
            raise ValueError(f"Shape mismatch: veg_on {veg_on_data.shape} vs veg_off {veg_off_data.shape}")

        print(f"  Shape: {veg_off_data.shape}")
        print(f"  Total emissions: {np.nansum(veg_off_data):,.0f} kg")

    # Calculate difference (vegetation_off - vegetation_on)
    print("\nCalculating difference (vegetation OFF - vegetation ON)...")
    difference = veg_off_data - veg_on_data

    total_diff = np.nansum(difference)
    print(f"  Total difference: {total_diff:,.0f} kg")
    print(f"  Mean difference: {np.nanmean(difference):.2e} kg/pixel")

    # Count pixels with increases vs decreases
    positive_mask = difference > 0
    negative_mask = difference < 0
    n_increased = np.sum(positive_mask)
    n_decreased = np.sum(negative_mask)

    print(f"  Pixels with increased emissions: {n_increased:,} ({n_increased/difference.size*100:.1f}%)")
    print(f"  Pixels with decreased emissions: {n_decreased:,} ({n_decreased/difference.size*100:.1f}%)")

    if total_diff > 0:
        print(f"  ⚠️  Net INCREASE in dust emissions when vegetation removed")
    else:
        print(f"  ✓ Net DECREASE in dust emissions when vegetation removed")

    # Generate lat/lon coordinates from GeoTIFF transform
    print("\nGenerating coordinate arrays...")

    # For a regular grid, calculate coordinates directly from transform
    # Transform: (pixel_width, 0, x_min, 0, pixel_height, y_max)
    x_min = transform[2]
    y_max = transform[5]
    pixel_width = transform[0]
    pixel_height = transform[4]  # Usually negative

    # Generate 1D coordinate arrays
    lon_1d = x_min + (np.arange(width) + 0.5) * pixel_width
    lat_1d = y_max + (np.arange(height) + 0.5) * pixel_height

    print(f"  Lon range: {lon_1d.min():.2f} to {lon_1d.max():.2f}")
    print(f"  Lat range: {lat_1d.min():.2f} to {lat_1d.max():.2f}")

    # Check if latitude needs flipping (descending to ascending)
    if lat_1d[0] > lat_1d[-1]:
        print("  Flipping latitude from descending to ascending order...")
        lat_1d = lat_1d[::-1]
        difference = np.flipud(difference)

    # Replace NaN values with 0
    nan_count = np.isnan(difference).sum()
    if nan_count > 0:
        print(f"  Replacing {nan_count:,} NaN values with 0...")
        difference = np.nan_to_num(difference, nan=0.0)
    else:
        print("  No NaN values found.")

    # Create xarray Dataset
    print("\nCreating InMAP-compatible NetCDF...")

    ds_out = xr.Dataset(
        {
            "PM2_5": (["lat", "lon"], difference)
        },
        coords={
            "lat": lat_1d,
            "lon": lon_1d
        }
    )

    # Add CF-compliant coordinate attributes (required for QGIS/GIS software)
    ds_out['lat'].attrs = {
        'standard_name': 'latitude',
        'long_name': 'latitude',
        'units': 'degrees_north',
        'axis': 'Y'
    }

    ds_out['lon'].attrs = {
        'standard_name': 'longitude',
        'long_name': 'longitude',
        'units': 'degrees_east',
        'axis': 'X'
    }

    # Add metadata attributes for the data variable
    ds_out['PM2_5'].attrs = {
        'long_name': 'Annual PM2.5 dust emission difference',
        'units': 'kg/year',
        'description': 'Difference in dust emissions: vegetation OFF minus vegetation ON',
        'source': 'LUEP dust emission model',
        'note': 'NaN values replaced with 0; latitude in ascending order; positive values indicate increased emissions when vegetation removed'
    }

    ds_out.attrs = {
        'title': 'PM2.5 Dust Emission Difference - InMAP Compatible',
        'institution': 'Land Use Emissions Processor (LUEP)',
        'vegetation_on_file': veg_on_file,
        'vegetation_off_file': veg_off_file,
        'calculation': 'vegetation_off - vegetation_on',
        'total_difference_kg': float(total_diff),
        'Conventions': 'CF-1.6'
    }

    print(f"\nSaving InMAP-compatible file to: {output_file}")
    print(f"  Variable name: PM2_5")
    print(f"  Lat range: {float(ds_out.lat.min()):.2f} to {float(ds_out.lat.max()):.2f}")
    print(f"  Lon range: {float(ds_out.lon.min()):.2f} to {float(ds_out.lon.max()):.2f}")
    print(f"  Format: NETCDF3_64BIT_OFFSET")

    # Save as NETCDF-3 64-bit offset format (supports files >2GB, InMAP compatible)
    ds_out.to_netcdf(
        output_file,
        format='NETCDF3_64BIT_OFFSET',
        engine='netcdf4'
    )

    print("\n✓ Conversion complete!")
    print(f"  Output file: {output_file}")
    print(f"  File format: NETCDF-3 (64-bit offset)")
    print(f"  Variable: PM2_5")
    print(f"  Shape: {ds_out['PM2_5'].shape}")
    print(f"  Total difference: {total_diff:,.0f} kg/year")
    print("="*80)


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) != 4:
        print(__doc__)
        print("\nError: Incorrect number of arguments")
        print(f"Usage: {sys.argv[0]} <vegetation_on_file> <vegetation_off_file> <output_file>")
        sys.exit(1)

    veg_on_file = sys.argv[1]
    veg_off_file = sys.argv[2]
    output_file = sys.argv[3]

    try:
        calculate_dust_difference_inmap(veg_on_file, veg_off_file, output_file)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
