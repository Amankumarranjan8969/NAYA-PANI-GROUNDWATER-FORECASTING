# Generates test_photoreal_twin.html
import json, os

static_dir = r'D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\static'
with open(os.path.join(static_dir, 'elevation_luni_50km.json'), 'r') as fp:
    dem = json.load(fp)

elev_compact = [[round(y, 1) for y in row] for row in dem['elevations']]
dem_json_str = json.dumps({'grid_size': dem['grid_size'], 'min_elev': dem['min_elev'], 'max_elev': dem['max_elev'], 'elevations': elev_compact})

print('Generating full photoreal HTML with embedded DEM...')
