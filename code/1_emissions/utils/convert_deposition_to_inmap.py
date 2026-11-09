#!/usr/bin/env python3
"""
Convert PM2.5 deposition NetCDF files to InMAP-compatible format.

This script converts LUEP deposition output files to meet InMAP requirements:
1. NETCDF-3 64-bit offset format (supports large files >2GB, InMAP compatible)
2. Latitude coordinates in ascending order (south to north: -90 to +90)
3. Variable name "PM2_5" instead of "annual_PM2.5_deposition"
4. All NaN/missing values replaced with 0
5. CF-compliant coordinate attributes (units, standard_name) for QGIS compatibility

Usage:
    python utils/convert_deposition_to_inmap.py <input_file> <output_file>

Example:
    python utils/convert_deposition_to_inmap.py \\
        outputs/PM2.5_annual_deposition_2019.nc \\
        outputs/PM2.5_deposition_2019_inmap.nc
"""

import sys
import xarray as xr
import numpy as np


def convert_to_inmap_format(input_file, output_file):
    """
    Convert deposition NetCDF to InMAP-compatible format.

    Parameters:
    -----------
    input_file : str
        Path to input NetCDF file (LUEP deposition output)
    output_file : str
        Path to output NetCDF file (InMAP-compatible format)
    """
    print(f"Loading deposition data from: {input_file}")

    # Open the dataset
    with xr.open_dataset(input_file) as ds:
        # Get the deposition variable (handle both possible names)
        if 'annual_PM2.5_deposition' in ds:
            deposition = ds['annual_PM2.5_deposition']
        elif 'PM2_5' in ds:
            deposition = ds['PM2_5']
        else:
            raise ValueError(f"Could not find deposition variable in {input_file}")

        print(f"  Original variable name: {deposition.name}")
        print(f"  Original shape: {deposition.shape}")
        print(f"  Original lat range: {float(deposition.lat.min()):.2f} to {float(deposition.lat.max()):.2f}")

        # Check if latitude needs flipping (descending to ascending)
        if deposition.lat[0] > deposition.lat[-1]:
            print("  Flipping latitude from descending to ascending order...")
            deposition = deposition.isel(lat=slice(None, None, -1))

        # Replace NaN values with 0
        nan_count = np.isnan(deposition.values).sum()
        if nan_count > 0:
            print(f"  Replacing {nan_count:,} NaN values with 0...")
            deposition = deposition.fillna(0)
        else:
            print("  No NaN values found.")

        # Create new dataset with renamed variable
        ds_out = xr.Dataset(
            {
                "PM2_5": deposition
            },
            coords={
                "lat": deposition.lat,
                "lon": deposition.lon
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
            'long_name': 'Annual PM2.5 deposition',
            'units': 'kg/year',
            'description': 'PM2.5 deposition from vegetation, converted to InMAP format',
            'source': 'LUEP deposition model',
            'note': 'NaN values replaced with 0; latitude in ascending order'
        }

        ds_out.attrs = {
            'title': 'PM2.5 Deposition - InMAP Compatible',
            'institution': 'Land Use Emissions Processor (LUEP)',
            'source_file': input_file,
            'Conventions': 'CF-1.6'
        }

        print(f"\nSaving InMAP-compatible file to: {output_file}")
        print(f"  Variable name: PM2_5")
        print(f"  Lat range: {float(ds_out.lat.min()):.2f} to {float(ds_out.lat.max()):.2f}")
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


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) != 3:
        print(__doc__)
        print("\nError: Incorrect number of arguments")
        print(f"Usage: {sys.argv[0]} <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        convert_to_inmap_format(input_file, output_file)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
