
import json, os

with open(r'D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\static\elevation_luni_50km.json', 'r') as f:
    dem = json.load(f)

# Compact the elevations to 1 decimal place to save size if embedded
elev_compact = [[round(y, 1) for y in row] for row in dem['elevations']]
dem_json_str = json.dumps({'grid_size': dem['grid_size'], 'min_elev': dem['min_elev'], 'max_elev': dem['max_elev'], 'elevations': elev_compact})

print('Dem json compacted size:', len(dem_json_str))
