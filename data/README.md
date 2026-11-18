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
- Turnaround (drawn in the all-stops map - the 7E leg continues past Gabus Raya
  to Flyover Raya Bogor and the Ragunan-bound return runs back up the left side
  past Baung to Phe Tower Kebagusan beside the venue; a single venue marker
  between the two directions carries the dashed walks, and the road between the
  directions is drawn there with the pedestrian bridge between the Mujair and
  Phe Tower stops; plus a text card in the Arkadia section): the Flyover
  Raya Bogor stop name appears in both 7E direction listings - Kampung
  Rambutan-bound stop 14 of 21, Ragunan-bound stop 8 of 24 - and it is the first
  stop past Jln. Gabus Raya shared by both patterns, so the shortest candidate
  turnaround on paper (the physical interchange is not verified). Verified 18 Nov
  2026
  from Catenary's GTFS rendering
  (https://catenarymaps.org/en/agency/Transjakarta/route/7e), cross-checked with
  jaGOdetabek (https://jagodetabek.id/lin/TJ7E, stop G00315). The official feed
  had no DNS A record at that moment, so the return-leg stop names are not in
  route-stops.json. Firsthand on-site check the same day: the two 7E directions
  stop on opposite road sides by the venue - Jln. Gabus Raya (Kampung
  Rambutan-bound) is across the road, reached by a short walk back
  via the pedestrian bridge between the Mujair and Phe Tower stops - while the venue sits
  beside Phe Tower Kebagusan (Ragunan-bound); Jln. Gabus Raya (far side) and
  Baung (venue side) are both farther along toward Kampung Rambutan. The dashed switch in the
  map still marks an unverified physical link, and the map otherwise stays
  listed-direction-only.

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

## Arkadia homebound options (0.1.5)

`return-stops.json` stores independently listed directional sequences from Catenary's
TransJakarta GTFS rendering, checked 18 November 2026. It is not a new official
feed download: that host could not be resolved. Each segment records its source URL.
7E starts beside the venue toward Ragunan. The northbound 6 includes Flyover
Kuningan; the 4 homeward leg uses the listed Pulo Gadung pattern, not a reversed
outbound route. The separate Gojek alternative joins 7F at Flyover Raya Bogor. The 7F
Juanda-direction order is cross-checked against an e-kompas route listing
(2024-05-08,
https://e-kompas.id/rute-transjakarta-7f-kampung-rambutan-juanda-dan-halte-pemberhentiannya-e-kompas-id-otomotif/):
same six-stop order from Flyover Raya Bogor to Kayu Putih Rawasari, whose last
three names match the first three stops of the official 10 pattern, so the map
draws those station areas once on a shared two-way spine.
Both are drawn below the outbound schematic in the same SVG and offline asset.
No precise Ragunan transfer access, paid-area continuity, ride time, empty bus,
seat availability or late 7F operation is promised. Existing firsthand fare
observations for the earlier outbound journey remain unchanged.
