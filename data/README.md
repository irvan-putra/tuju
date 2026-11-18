# Selected outbound stop sequences

Stop names, IDs and order are from the TransJakarta operator GTFS feed:
https://gtfs.transjakarta.co.id/files/file_gtfs.zip

Downloaded and checked 18 November 2026. `route-stops.json` records the feed's
SHA-256, selected trip IDs, exact stop IDs and original sequence numbers. Only
relevant segments are retained; the full feed is not bundled. These are scheduled
patterns, not proof a bus is operating now. Never reverse a sequence to invent the
return journey. The selected patterns matter:

- 4: `4-R26`, Galunggung via Saharjo, includes Matraman and Pasar Rumput.
  Other corridor 4 patterns can skip these stops.
- 6: `6-R04`, Galunggung toward Ragunan, get off at Simpang Ragunan Ar-Raudhah.
- 7E: `7E-R05`, Kampung Rambutan-bound, Masjid Ar-Raudhah to Jln. Gabus Raya.
  Phe Tower Kebagusan and Baung belong to the opposite direction, not this leg.
- 10: `10-R01`, PGC-bound, Kayu Putih Rawasari to Cawang Sentral.
- 9: `9-R01`, Pluit-bound, Cawang Sentral to Tanjung Duren Arah Barat.
- 4C: `4C-R09`, Bundaran Senayan-bound, Pramuka BPKP 2 to Tugu Proklamasi.
- 5M: `5M-L04`, Tanah Abang via Cikini loop, Matraman 3 to JPO Blok E.
  Other variants differ. Operator notice independently confirms Matraman 3 rather
  than Simpang Matraman for the 5M boarding:
  https://transjakarta.co.id/berita/penyesuaian-rute-kampung-melayu-tanah-abang-via-cikini-5m

The 4C and 5M share Masjid Jami Matraman and Tugu Proklamasi; the diagram draws
those shared stops once. The corridor 10-to-9 change uses different platform IDs
at Cawang Sentral, not a reversed trip. Galunggung has different boarding records
for 4 and 6, so the existing unconfirmed paid-area continuity caveat remains.
Walking distances and destination closeups are retained from the existing page,
not derived from GTFS. GTFS supplies neither walking distances nor fare-policy
assurances. Older aggregator lists differ, so they are not merged into this map.

## Rebuild

```
python tools/import_stops.py /path/to/file_gtfs.zip
python tools/build_route_map.py
python android/tools/build_map_asset.py
python tools/test_route_map.py
python android/tools/build_map_asset.py --check
```

Review trip IDs, directional endpoints and source changes before refreshing. The
map deliberately starts fit-to-screen; pinch zoom is needed to read all labels on
a phone. SVG text stays sharp when zoomed. No added app permissions or network.
