#!/usr/bin/env python3
"""
Regrid PM2.5 deposition to match dust emission grid resolution.

This script regrids high-resolution deposition data to match the coarser dust
emission grid. CRITICAL: Uses SUM aggregation (not averaging) because data is
in kg/year per pixel, not kg/year per m².

When combining multiple fine-resolution pixels into one coarse pixel:
- CORRECT: Sum all underlying pixel values (preserves total mass)
- WRONG: Average underlying pixel values (loses 99% of mass!)

Usage:
    python utils/regrid_deposition_to_dust.py <deposition_file> <dust_file> <output_file>

Example:
    python utils/regrid_deposition_to_dust.py \\
        outputs/PM2.5_deposition_2019_inmap.nc \\
        outputs/dust_difference_2019_inmap.nc \\
        outputs/PM2.5_deposition_2019_regridded.nc

Input:
    - Deposition file: High-resolution (e.g., 18000×36000 pixels, 0.01°)
    - Dust file: Target grid resolution (e.g., 1708×3600 pixels, 0.1°)

Output:
    - Regridded deposition matching dust grid resolution
    - InMAP-compatible format (NETCDF-3 64-bit offset)
    - Total mass preserved (within numerical precision)
"""

import sys
import xarray as xr
import numpy as np


def regrid_deposition_to_dust(deposition_file, dust_file, output_file):
    """
    Regrid deposition data to match dust emission grid.

    Parameters:
    -----------
    deposition_file : str
        Path to high-resolution deposition NetCDF file
    dust_file : str
        Path to dust emission NetCDF file (defines target grid)
    output_file : str
        Path to output regridded NetCDF file
    """
    print("="*80)
    print("REGRID DEPOSITION TO DUST GRID RESOLUTION")
    print("="*80)

    # Load dust file to get target grid
    print(f"\nLoading target grid from dust file: {dust_file}")
    with xr.open_dataset(dust_file) as ds_dust:
        target_lat = ds_dust.lat.values
        target_lon = ds_dust.lon.values

        print(f"  Target grid shape: {len(target_lat)} lat × {len(target_lon)} lon")
        print(f"  Target lat range: {target_lat.min():.2f}° to {target_lat.max():.2f}°")
        print(f"  Target lon range: {target_lon.min():.2f}° to {target_lon.max():.2f}°")

        # Calculate target resolution
        if len(target_lat) > 1:
            target_lat_res = np.abs(target_lat[1] - target_lat[0])
        else:
            target_lat_res = 1.0

        if len(target_lon) > 1:
            target_lon_res = np.abs(target_lon[1] - target_lon[0])
        else:
            target_lon_res = 1.0

        print(f"  Target resolution: {target_lon_res:.4f}° lon × {target_lat_res:.4f}° lat")

    # Load deposition file
    print(f"\nLoading deposition file: {deposition_file}")
    with xr.open_dataset(deposition_file) as ds_dep:
        if 'PM2_5' not in ds_dep:
            raise ValueError(f"Variable 'PM2_5' not found in {deposition_file}")

        source_lat = ds_dep.lat.values
        source_lon = ds_dep.lon.values

        print(f"  Source grid shape: {len(source_lat)} lat × {len(source_lon)} lon")
        print(f"  Source lat range: {source_lat.min():.2f}° to {source_lat.max():.2f}°")
        print(f"  Source lon range: {source_lon.min():.2f}° to {source_lon.max():.2f}°")

        # Calculate source resolution
        if len(source_lat) > 1:
            source_lat_res = np.abs(source_lat[1] - source_lat[0])
        else:
            source_lat_res = 1.0

        if len(source_lon) > 1:
            source_lon_res = np.abs(source_lon[1] - source_lon[0])
        else:
            source_lon_res = 1.0

        print(f"  Source resolution: {source_lon_res:.4f}° lon × {source_lat_res:.4f}° lat")

        # Check total mass before regridding
        total_before = float(ds_dep.PM2_5.sum())
        print(f"  Total mass before regridding: {total_before:,.0f} kg/year")

        # Calculate coarsening factors
        # How many fine pixels fit into one coarse pixel?
        lat_factor = int(np.round(target_lat_res / source_lat_res))
        lon_factor = int(np.round(target_lon_res / source_lon_res))

        print(f"\nRegridding parameters:")
        print(f"  Latitude coarsening factor: {lat_factor}×")
        print(f"  Longitude coarsening factor: {lon_factor}×")
        print(f"  Total pixel reduction: {lat_factor * lon_factor}× fewer pixels")
        print(f"  Aggregation method: SUM (preserves total mass)")

        if lat_factor == 1 and lon_factor == 1:
            print("\n⚠️  Warning: Grids already match - no regridding needed!")
            print("  Copying deposition file to output...")
            ds_dep.to_netcdf(output_file, format='NETCDF3_64BIT_OFFSET', engine='netcdf4')
            return

        # Trim source data to be evenly divisible by coarsening factors
        # This ensures clean aggregation without partial pixels
        n_lat = (len(source_lat) // lat_factor) * lat_factor
        n_lon = (len(source_lon) // lon_factor) * lon_factor

        if n_lat != len(source_lat) or n_lon != len(source_lon):
            print(f"\n⚠️  Trimming source grid for even division:")
            print(f"    Original: {len(source_lat)} × {len(source_lon)}")
            print(f"    Trimmed:  {n_lat} × {n_lon}")

            ds_dep_trimmed = ds_dep.isel(lat=slice(0, n_lat), lon=slice(0, n_lon))
        else:
            ds_dep_trimmed = ds_dep

        # Perform coarsening with SUM aggregation
        print(f"\nCoarsening grid (this may take a moment for large files)...")

        ds_coarse = ds_dep_trimmed.coarsen(
            lat=lat_factor,
            lon=lon_factor,
            boundary='trim'  # Drop edge pixels if needed
        ).sum()

        # Check total mass after regridding
        total_after = float(ds_coarse.PM2_5.sum())
        mass_diff = total_after - total_before
        mass_pct_diff = (mass_diff / total_before * 100) if total_before > 0 else 0

        print(f"\n  Regridded grid shape: {ds_coarse.PM2_5.shape}")
        print(f"  Total mass after regridding: {total_after:,.0f} kg/year")
        print(f"  Mass difference: {mass_diff:,.0f} kg/year ({mass_pct_diff:+.3f}%)")

        if abs(mass_pct_diff) > 1.0:
            print(f"  ⚠️  Warning: Mass not conserved! Difference: {mass_pct_diff:.1f}%")
        else:
            print(f"  ✓ Mass conserved (within {abs(mass_pct_diff):.3f}%)")

        # Interpolate to exactly match target grid coordinates
        # This handles small coordinate differences (e.g., -179.95 vs -179.9)
        print(f"\nInterpolating to match target coordinates exactly...")

        ds_regridded = ds_coarse.interp(
            lat=target_lat,
            lon=target_lon,
            method='nearest'  # Use nearest to avoid introducing values where there was none
        )

        # Check mass after interpolation
        total_interp = float(ds_regridded.PM2_5.sum())
        interp_diff = total_interp - total_after
        interp_pct_diff = (interp_diff / total_after * 100) if total_after > 0 else 0

        print(f"  Total after interpolation: {total_interp:,.0f} kg/year")
        print(f"  Interpolation difference: {interp_diff:,.0f} kg/year ({interp_pct_diff:+.3f}%)")

        # Verify no NaN values were introduced
        nan_count = int(ds_regridded.PM2_5.isnull().sum())
        if nan_count > 0:
            print(f"\n  ⚠️  Replacing {nan_count:,} NaN values with 0...")
            ds_regridded['PM2_5'] = ds_regridded['PM2_5'].fillna(0)
        else:
            print(f"  ✓ No NaN values")

        # Add InMAP-compliant coordinate attributes
        print(f"\nApplying InMAP format requirements...")

        ds_regridded['lat'].attrs = {
            'standard_name': 'latitude',
            'long_name': 'latitude',
            'units': 'degrees_north',
            'axis': 'Y'
        }

        ds_regridded['lon'].attrs = {
            'standard_name': 'longitude',
            'long_name': 'longitude',
            'units': 'degrees_east',
            'axis': 'X'
        }

        # Preserve PM2_5 variable attributes and add regridding info
        original_attrs = ds_dep.PM2_5.attrs.copy()
        ds_regridded['PM2_5'].attrs = original_attrs
        ds_regridded['PM2_5'].attrs['regridded'] = 'true'
        ds_regridded['PM2_5'].attrs['regrid_method'] = 'coarsen with sum aggregation'
        ds_regridded['PM2_5'].attrs['regrid_factors'] = f'{lat_factor}x lat, {lon_factor}x lon'
        ds_regridded['PM2_5'].attrs['original_resolution'] = f'{source_lon_res}° × {source_lat_res}°'
        ds_regridded['PM2_5'].attrs['regridded_resolution'] = f'{target_lon_res}° × {target_lat_res}°'

        # Preserve global attributes and add regridding info
        ds_regridded.attrs = ds_dep.attrs.copy()
        ds_regridded.attrs['regridded_from'] = deposition_file
        ds_regridded.attrs['regrid_target_grid'] = dust_file
        ds_regridded.attrs['regrid_method'] = 'coarsen with sum aggregation'

        # Save as NETCDF-3 64-bit offset format
        print(f"\nSaving regridded file: {output_file}")
        print(f"  Format: NETCDF3_64BIT_OFFSET (InMAP-compatible)")

        ds_regridded.to_netcdf(
            output_file,
            format='NETCDF3_64BIT_OFFSET',
            engine='netcdf4'
        )

        # Calculate file size reduction
        import os
        if os.path.exists(deposition_file) and os.path.exists(output_file):
            size_before = os.path.getsize(deposition_file) / (1024**3)  # GB
            size_after = os.path.getsize(output_file) / (1024**3)  # GB
            size_reduction = (1 - size_after / size_before) * 100

            print(f"\nFile size comparison:")
            print(f"  Original: {size_before:.2f} GB")
            print(f"  Regridded: {size_after:.2f} GB")
            print(f"  Reduction: {size_reduction:.1f}%")

        print(f"\n✓ Regridding complete!")
        print(f"  Output: {output_file}")
        print(f"  Grid: {ds_regridded.PM2_5.shape}")
        print(f"  Total: {total_interp:,.0f} kg/year")
        print(f"  Mass conserved: {abs(total_interp - total_before) / total_before * 100:.3f}% difference")
        print(f"  Ready for InMAP")
        print("="*80)


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) != 4:
        print(__doc__)
        print("\nError: Incorrect number of arguments")
        print(f"Usage: {sys.argv[0]} <deposition_file> <dust_file> <output_file>")
        sys.exit(1)

    deposition_file = sys.argv[1]
    dust_file = sys.argv[2]
    output_file = sys.argv[3]

    try:
        regrid_deposition_to_dust(deposition_file, dust_file, output_file)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
