"""Build one printable A4 PDF per trip day into daily/pdf/.

Run:  python daily/build.py
Needs Chrome or Edge for printing.
"""
import html
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "html")
OUT_PDF = os.path.join(HERE, "pdf")

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

# Confirmation emails in Simon's Gmail. References in subjects are replaced with "…".
# key: (subject, sender, received (Irish time))
EMAILS = {
    "premier": ("Your booking is confirmed. Ref no. …", "Premier Inn", "19 Aug, 09:52"),
    "aer": ("Aer Lingus Confirmation - Booking Ref: …", "Aer Lingus", "6 Sep, 11:40"),
    "qatar": ("Booking confirmation : …", "Qatar Airways", "16 Aug, 18:09"),
    "george": ("Your Confirmed Booking at George (Southwark)", "Greene King", "29 Aug, 20:39"),
    "tower": ("Expian Ticket Summary - …", "Historic Royal Palaces", "29 Aug, 16:03"),
    "elpastor": ("Your Reservation at El Pastor London Bridge | Simon O'Donovan on 06/10/2026", "SevenRooms", "14 Sep, 22:17"),
    "stpauls": ("St Paul's Cathedral Sightseeing Tickets", "St Paul's Cathedral", "29 Aug, 16:31"),
    "marquis": ("The Marquis Cornwallis | Booking Confirmation (DMN-…)", "Collins Bookings", "27 Aug, 21:28"),
    "wb": ("Booking Confirmation and Tickets - Order number: …", "WB Studio Tour", "24 Aug, 21:00"),
    "nhm": ("Natural History Museum Order #…", "Natural History Museum", "29 Aug, 19:08"),
    "caravan": ("Your Reservation at Caravan Covent Garden | Simon O'Donovan on 08/10/2026", "SevenRooms", "29 Aug, 19:03"),
    "totoro": ("Thank You For Booking With LW Tickets", "LW Tickets", "25 Aug, 19:47"),
    "hunterian": ("Order Confirmation for Hunterian Museum - Free timed entry October 2026", "Eventbrite",
                  "29 Aug, 19:31"),
    "cafe": ("Your booking confirmation for Le Cafe du Marche", "OpenTable", "27 Aug, 19:47"),
    "boundary": ("Your Reservation at Boundary Rooftop | Simon O'Donovan on 11/10/2026", "SevenRooms", "12 Sep, 17:23"),
    "lner1": ("Your reservation from London Kings Cross to York is confirmed!", "LNER", "6 Sep, 13:13"),
    "tlyork": ("Your Travelodge booking confirmation", "Travelodge", "6 Sep, 20:21"),
    "rustique": ("Rustique Restaurant | Booking Confirmation (DMN-…)", "Collins Bookings", "19 Sep, 15:53"),
    "cocoa": ("Confirmation: Chocolate Bar Making at York Cocoa Works on Tuesday, 13 October 2026 @ 2:30pm - 3:45pm",
              "FareHarbor", "10 Sep, 22:31"),
    "ambiente": ("Your Reservation at Ambiente Fossgate | Simon O'Donovan on 13/10/2026", "SevenRooms", "12 Sep, 12:24"),
    "lner2": ("Your reservation from York to Edinburgh is confirmed!", "LNER", "6 Sep, 18:04"),
    "tledi": ("Your Travelodge booking confirmation", "Travelodge", "6 Sep, 16:58"),
    "devils": ("The Devil's Advocate Bar & Kitchen | Booking Confirmation (DMN-…)", "Collins Bookings",
               "12 Sep, 10:32"),
    "sheep": ("Your Booking is Confirmed at The Sheep Heid Inn on Thursday, 15th October 2026", "mycountrypub",
              "10 Sep, 22:18"),
    "angels": ("Your booking confirmation for Angels with Bagpipes", "OpenTable", "12 Sep, 15:03"),
    "hes": ("Historic Environment Scotland Order …", "Historic Environment Scotland", "19 Sep, 13:40"),
    "mkc": ("Thank you for booking your tour at The Real Mary King's Close", "Real Mary King's Close", "8 Sep, 21:49"),
    "moxy": ("Reservation Confirmation #… for Moxy Edinburgh Airport", "Marriott", "6 Sep, 18:42"),
    "ryanair": ("Ryanair Travel Itinerary", "Ryanair", "5 Sep, 14:39"),
}

# Timeline row kinds: do (activity), go (travel), eat (booked or planned meal), opt (optional), key (hard deadline)
DAYS = [
    dict(
        n=1, slug="day01-sun-04-oct", dow="Sunday", date="4 October", city="Cork → London",
        title="Simon flies over; Jenifer is in the air",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP",
              "Booked from tonight, so the room is ready when Jenifer lands."),
        anchors=[("16:10", "EI722 Cork → Heathrow"), ("18:35 Manila", "QR 933 departs")],
        timeline=[
            ("16:10", "key", "Aer Lingus EI722, Cork → London Heathrow",
             "Lands 17:35. Seat 7D, one 20 kg checked bag. The confirmation doesn't give the Heathrow terminal, so check it on the day."),
            ("~17:45", "go", "Heathrow → hotel, about 1 hr 15 min",
             "Elizabeth line eastbound (toward Abbey Wood/Shenfield) to Farringdon, about 45 min. Change to Thameslink southbound, 3 stops to London Bridge. "
             "Borough High Street exit; the hotel is 4 min south on the left, at no. 135. Contactless, about £14."),
            ("~19:15", "do", "Check in", ""),
            ("Evening", "opt", "Millennium Bridge, 20 min, only if you have the energy",
             "Five minutes to the river and over the bridge for St Paul's lit up, then home. Something quick to eat: "
             "Flat Iron Square, The Anchor Bankside or Padella, all within 5 min."),
            ("Bed", "key", "Alarm for about 05:00", "QR 011 lands at Heathrow T4 at 06:25."),
            ("Meanwhile", "do", "Jenifer: QR 933 Manila T3 18:35 → Doha 22:50",
             "Then QR 011 Doha 01:10 → Heathrow T4 06:25 Monday. Seats 22G / 52G."),
        ],
        bookings=[
            ("Aer Lingus EI722 (Simon)", "Sun 4 Oct, 16:10 ORK → 17:35 LHR", "aer"),
            ("Qatar Airways QR 933 / QR 011 (Jenifer)", "Sun 4 Oct 18:35 MNL → Mon 5 Oct 06:25 LHR T4", "qatar"),
            ("Premier Inn Southwark, 8 nights", "4 → 12 Oct", "premier"),
        ],
        notes=["Heathrow border pack for Monday morning: printed separately (see the borders page)."],
    ),
    dict(
        n=2, slug="day02-mon-05-oct", dow="Monday", date="5 October", city="London",
        title="Arrival, then a slow first day",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("06:25", "QR 011 lands T4"), ("~17:00", "London Eye (decide 15:30)"), ("18:00", "The George Inn")],
        timeline=[
            ("06:25", "key", "QR 011 lands at Heathrow Terminal 4", "Simon meets Jenifer at arrivals."),
            ("~07:00", "go", "Heathrow T4 → hotel, about 1 hr",
             "Elizabeth line eastbound to Farringdon, then Thameslink 3 stops to London Bridge, 4 min walk. Contactless, about £14 each."),
            ("~08:00", "do", "In the room. Shower, breakfast, sleep", "Nothing is planned before noon."),
            ("~13:00", "eat", "Light lunch around Borough Market (4 min)",
             "The stalls are shut on Mondays; Monmouth Coffee (2 Park St) and Bread Ahead (Cathedral St) are open."),
            ("Afternoon", "do", "Four free things within 5 min of the door",
             "Southwark Cathedral (20 min) · Winchester Palace ruin and the Golden Hinde, Clink St (15 min) · Crossbones Graveyard, Redcross Way (10 min)."),
            ("15:30", "key", "Decide on the London Eye",
             "If she's up for it, buy the last rotation online (londoneye.com, about £30pp; skip Fast Track). Nothing later than 17:00, "
             "because the George table is at 18:00."),
            ("16:30", "go", "Walk west along the South Bank, 25 min",
             "Past Tate Modern and the Millennium Bridge, under Blackfriars and Waterloo Bridges."),
            ("~17:00", "opt", "London Eye, last rotation, 30 min",
             "County Hall, SE1 7PB. If she's flat, skip it and walk the South Bank to Blackfriars instead."),
            ("17:35", "go", "Back east, 25 min walk",
             "Or the Jubilee line, Waterloo → London Bridge (2 stops)."),
            ("18:00", "eat", "Dinner: The George Inn, booked",
             "75 Borough High St, 2 min from the hotel. 2-hour table, back by 20:00 when busy. Bed by 21:00."),
        ],
        bookings=[
            ("The George Inn", "Mon 5 Oct, 18:00, 2 people, 2 hrs", "george"),
        ],
        notes=["The Old Operating Theatre is shut Mon–Wed; it's on Thursday."],
    ),
    dict(
        n=3, slug="day03-tue-06-oct", dow="Tuesday", date="6 October", city="London",
        title="The City and the Tower, all on foot",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("14:00", "Tower of London"), ("17:30", "Garden at 120"), ("19:30", "El Pastór")],
        timeline=[
            ("Morning", "do", "Lie-in, then Borough Market at full strength",
             "8 Southwark St, 4 min walk. Open Tue–Fri 10:00–17:00. Graze; lunch is at Leadenhall."),
            ("~11:30", "go", "Over London Bridge into the City, 15 min walk", "No tube all day."),
            ("Late AM", "do", "Leadenhall Market and St Dunstan in the East",
             "Both free. Leadenhall was Diagon Alley in the first film; St Dunstan is a Blitz ruin taken over by a garden."),
            ("~12:45", "eat", "Proper sit-down lunch under the Leadenhall roof", "Don't skip it."),
            ("14:00", "key", "Tower of London",
             "Tower Hill, EC3N 4AB. All-day ticket, so 14:00 is the plan rather than a deadline. Last admission 16:30. "
             "Join a Yeoman Warder tour on arrival (every 30 min, free), then the Crown Jewels, White Tower and ravens. About 2.5 hrs."),
            ("~16:30", "do", "Walk across Tower Bridge",
             "Free. The Exhibition with the glass floor is optional: £18 each, last entry 17:00. Check bascule lift times at towerbridge.org.uk."),
            ("17:30", "do", "Garden at 120, 120 Fenchurch St",
             "Free, no booking. Rooftop on the 15th floor. Shuts 18:30; sunset 18:35. Bring a coat."),
            ("18:30", "go", "Thames Path home in the dark, about 25 min", "Back about 19:00."),
            ("19:30", "eat", "Dinner: El Pastór, booked",
             "7A Stoney Street, SE1 9AA, 6 min from the hotel. 19:30–21:00. Table held 15 min. Cancelling inside 12 hrs costs £20pp."),
        ],
        bookings=[
            ("Tower of London, 2 adults", "Tue 6 Oct, all-day admission", "tower"),
            ("El Pastór, Borough Market", "Tue 6 Oct, 19:30–21:00, 2 guests", "elpastor"),
        ],
        notes=["Early night: tomorrow is St Paul's at 10:00 and Leavesden until 20:30."],
    ),
    dict(
        n=4, slug="day04-wed-07-oct", dow="Wednesday", date="7 October", city="London",
        title="St Paul's, then the Studio Tour",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("10:00", "St Paul's"), ("13:00", "Marquis Cornwallis"), ("15:00", "Train, Euston"),
                 ("16:30", "Studio Tour")],
        timeline=[
            ("09:50", "go", "Hotel → St Paul's, 10 min walk", "Over the Millennium Bridge."),
            ("10:00", "key", "St Paul's Cathedral, dome climb",
             "Enter by the West Entrance or the North Transept (step-free). 257 steps to the Whispering Gallery, 528 to the Golden Gallery. "
             "Crypt: Nelson, Wellington, Wren. About 2 hrs. The dome is optional if the morning runs long; the afternoon is 4 hrs on your feet."),
            ("~12:00", "do", "Postman's Park, King Edward St, 2 min north", "15 min. Tiles for everyday heroes."),
            ("12:25", "go", "Leave the park: 30 min walk to Marchmont Street",
             "Holborn Viaduct → Theobald's Rd → Guilford St → Russell Square. Short on time? Central line to Holborn, then Piccadilly to Russell Square, about 20 min."),
            ("13:00", "eat", "Long lunch: The Marquis Cornwallis, booked 13:00–14:30",
             "31 Marchmont St, WC1N 1AP. Held 15 min; 90 minutes only, so order promptly. This is the main meal of the day."),
            ("14:30", "go", "Walk to Euston, 12 min",
             "North to Tavistock Place, then west to the station."),
            ("By 15:00", "key", "Train Euston → Watford Junction, about 20 min",
             "West Coast line, contactless, about £12pp return. Then the Mullany's shuttle bus to the studios, 15 min, every 20 min. Aim to arrive about 16:00."),
            ("16:30", "key", "Warner Bros. Studio Tour, Dark Arts",
             "Studio Tour Drive, Leavesden, WD25 7LR. No entry before 16:10. Self-paced, about 4 hrs; you reach the Backlot about 19:00, after dark. "
             "Butterbeer at the Backlot Café."),
            ("~20:30", "go", "Shuttle → Watford Junction → Euston → hotel", "Back about 21:45."),
            ("Late", "opt", "Something small, if anything",
             "Bermondsey Street has the latest kitchens, or a nightcap at The Anchor Bankside."),
        ],
        bookings=[
            ("St Paul's Cathedral, 2 adults", "Wed 7 Oct, 10:00 entry", "stpauls"),
            ("The Marquis Cornwallis", "Wed 7 Oct, 13:00–14:30, 2 people", "marquis"),
            ("WB Studio Tour, 2 adults", "Wed 7 Oct, 16:30 entry", "wb"),
        ],
        notes=[],
    ),
    dict(
        n=5, slug="day05-thu-08-oct", dow="Thursday", date="8 October", city="London",
        title="Natural History Museum, then Totoro",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("10:30", "Natural History Museum"), ("17:00", "Caravan"), ("19:00", "Totoro")],
        timeline=[
            ("09:30", "opt", "If you're up early: St James's Park and Green Park",
             "Only if you're out by 09:30. From St James's Park station it's 4 stops on the District line to South Kensington."),
            ("10:00", "go", "Hotel → South Kensington, about 30 min",
             "Jubilee line London Bridge → Green Park, then the Piccadilly line to South Kensington. Use the museum subway from the station."),
            ("10:30", "key", "Natural History Museum",
             "Cromwell Road, SW7 5BD. Hintze Hall (blue whale) first, then the dinosaurs, then Earth Hall. Small bite inside about 12:15."),
            ("13:50", "go", "Leave. Piccadilly → Green Park → Jubilee → London Bridge", "In the room by about 14:25."),
            ("14:45", "opt", "The Old Operating Theatre, 6 min from the hotel",
             "9a St Thomas St, SE1 9RY. About £7.50pp, open Thu–Sun 10:30–17:00. 45 min, then back to change."),
            ("16:25", "go", "Hotel → Drury Lane, about 30 min",
             "Northern line London Bridge → Bank, then Central line to Holborn, 5 min walk."),
            ("17:00", "eat", "Dinner: Caravan Covent Garden, booked 17:00–18:30",
             "30–35 Drury Lane, next door to the theatre. Ask for the pre-theatre menu (£25 for 2 courses, £29 for 3). Card only."),
            ("19:00", "key", "My Neighbour Totoro, Gillian Lynne Theatre",
             "166 Drury Lane, WC2B 5PW. Stalls I41 and I42. About 2.5 hrs with interval."),
            ("~21:40", "go", "Home, about 40 min", "Holborn → Central → Bank → Northern → London Bridge. Back about 22:20."),
        ],
        bookings=[
            ("Natural History Museum, 2 adults (free slot)", "Thu 8 Oct, 10:30", "nhm"),
            ("Caravan Covent Garden", "Thu 8 Oct, 17:00–18:30, 2 guests", "caravan"),
            ("My Neighbour Totoro", "Thu 8 Oct, 19:00, stalls I41 & I42", "totoro"),
        ],
        notes=["Kew for Saturday isn't booked yet. Check the forecast today and book at kew.org if it looks dry."],
    ),
    dict(
        n=6, slug="day06-fri-09-oct", dow="Friday", date="9 October", city="London",
        title="Covent Garden, Seven Dials and Soho, then the dinner of the week",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("14:30", "Hunterian"), ("18:15", "Leave hotel"), ("19:00", "Le Café du Marché")],
        timeline=[
            ("09:30", "go", "Hotel → Holborn, about 30 min",
             "Northern line to Bank, then Central line to Holborn. Nothing before 14:30 is booked, so a lie-in is fine."),
            ("10:00", "do", "Neal's Yard and Seven Dials", "Go early; the yard is tiny. Neal's Yard Remedies on the corner."),
            ("10:40", "do", "Cecil Court, off Charing Cross Road", "Victorian alley of old booksellers; Watkins Books."),
            ("11:15", "eat", "Sweet stop 1: Maison Bertaux, 28 Greek St",
             "Share one slice; the only sit-down stop. The rule today: one thing per stop, shared."),
            ("11:55", "eat", "Stops 2–3: Venchi (James St), then Ladurée (Market Building)", "Walk through the piazza; don't stop in it."),
            ("12:35", "eat", "Stop 4: Bageriet, 24 Rose St", "One cardamom bun, shared."),
            ("13:00", "eat", "Seven Dials Market, 35 Earlham St: the savoury stop",
             "HOKO wonton noodle soup → Cucumber Alley dumplings → Chin Chin ice cream. Last food until dinner."),
            ("14:30", "key", "Hunterian Museum, free timed slot",
             "Royal College of Surgeons, 38–43 Lincoln's Inn Fields, WC2A 3PE. No backpacks (lockers first come). About an hour."),
            ("15:35", "go", "Holborn → hotel", "Central → Bank → Northern → London Bridge. In by about 16:05; two hours to change."),
            ("18:15", "go", "Hotel → Charterhouse Square, about 30 min",
             "Thameslink London Bridge → Farringdon (2 stops). Then 8 min up St John Street, under St John's Gate, left into Charterhouse Square. "
             "The restaurant is down the cobbled mews in the far corner; look for the arch."),
            ("19:00", "eat", "Dinner: Le Café du Marché, booked",
             "22 Charterhouse Mews, EC1M 6DX. Piano from 19:30. Kitchen winds down about 21:30; 20 min grace."),
            ("~21:30", "opt", "Nightcap: The Fox and Anchor, 115 Charterhouse St (quiet)",
             "Or Be At One, 40–42 Charterhouse St (lively)."),
            ("Home", "go", "Walk 35 min over the Millennium Bridge, or Thameslink Farringdon → London Bridge (6 min)",
             "If you have the nightcap, take the train. Tomorrow you leave for Kew at 09:15."),
        ],
        bookings=[
            ("Hunterian Museum, 2 tickets (free)", "Fri 9 Oct, 14:30–15:00 slot", "hunterian"),
            ("Le Café du Marché", "Fri 9 Oct, 19:00, table for 2", "cafe"),
        ],
        notes=["Novelty Automation (1a Princeton St, near Holborn, open to 18:00, about £5 in tokens) only if the afternoon runs short; it comes out of the change time."],
    ),
    dict(
        n=7, slug="day07-sat-10-oct", dow="Saturday", date="10 October", city="London",
        title="Kew, Petersham and Richmond Hill",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP", None),
        anchors=[("10:00", "Kew opens"), ("14:00", "Petersham Teahouse"), ("~18:12", "Sunset, Richmond Hill")],
        timeline=[
            ("09:15", "go", "Hotel → Kew Gardens, about 1 hr",
             "Jubilee line London Bridge → Westminster, then the District line toward Richmond, to Kew Gardens. 5 min walk to Victoria Gate."),
            ("10:00", "do", "Kew Gardens, about 3 hrs, one loop",
             "Palm House first (walkway at the top of the spiral stairs) → Waterlily House → Great Broad Walk Borders → Temperate House → "
             "Sackler Crossing → The Hive (lie on the glass floor) → Treetop Walkway."),
            ("~13:00", "go", "District line 2 stops to Richmond, then the towpath to Petersham, 25 min",
             "Walk down to Richmond Bridge and follow the Thames towpath south. Bus 65 if it's wet."),
            ("14:00", "eat", "Lunch: Petersham Nurseries Teahouse",
             "Church Ln, off Petersham Rd, TW10 7AB. Walk-in only, about £28pp. The Teahouse, not the Restaurant. Then the shop."),
            ("~15:30", "do", "Richmond Park, about 2 hrs",
             "In at Petersham Gate → Pembroke Lodge → King Henry's Mound (St Paul's through the hedge) → Pen Ponds → out at Richmond Gate. "
             "It's the deer rut: keep 50 m away."),
            ("~17:30", "do", "Richmond Hill at sunset (about 18:12)",
             "Terrace Gardens, TW10 6RN. The Roebuck is across the road; the Petersham Hotel if it's cold."),
            ("Evening", "eat", "Dinner in Richmond, 10 min down the hill", "Then District line home, about 45 min."),
        ],
        bookings=[
            ("Kew Gardens (not booked)", "Sat 10 Oct, from 10:00", None),
        ],
        notes=["Wet version: Kew until 14:00, lunch at Petersham, bus 65 into Richmond, then the Petersham Hotel lounge or home early."],
    ),
    dict(
        n=8, slug="day08-sun-11-oct", dow="Sunday", date="11 October", city="London",
        title="The East End: flowers, thrifting and a rooftop sunset",
        stay=("Premier Inn London Southwark (Borough High St)", "135 Borough High Street, SE1 1NP",
              "Last night here. Pack tonight."),
        anchors=[("08:45", "Columbia Road"), ("17:30", "Boundary Rooftop")],
        timeline=[
            ("~08:00", "go", "Hotel → Columbia Road",
             "Nearest stations: Hoxton (Overground) or Bethnal Green. Check the route on the morning; weekend engineering works are common."),
            ("08:45", "do", "Columbia Road Flower Market (Sundays only)",
             "Buy her flowers. Vintage Heaven (no. 82) and the Cake Hole tearoom; coffee on Ezra Street; Angela Flanders perfumer, no. 96."),
            ("~10:45", "go", "Walk south to Brick Lane, 10 min", ""),
            ("11:00", "do", "Brick Lane and the Old Truman Brewery, about 3 hrs",
             "Vintage Market (basement), Blitz (55 Hanbury St), Absolute Vintage, Rokit / Beyond Retro / Atika (Cheshire St), Rough Trade East."),
            ("Anytime", "eat", "Dark Sugars (141 Brick Lane), Beigel Bake (159 Brick Lane)",
             "Hot chocolate under shaved chocolate; salt beef bagel about £5."),
            ("14:00", "do", "Hanbury Street murals and Fournier Street", "1720s Huguenot silk-weavers' houses. 30 min."),
            ("15:00", "eat", "Old Spitalfields and Petticoat Lane (Middlesex St)",
             "Graze through the Spitalfields food stalls: Humble Crumble, Crosstown."),
            ("~17:15", "go", "Walk to Redchurch Street, about 12 min", "Up through Spitalfields, Brick Lane, left at the top."),
            ("17:30", "eat", "Boundary Rooftop, glass Orangery, booked",
             "2–4 Boundary St, entrance on Redchurch St, E2 7DD. Sunset 18:10. Kitchen to 23:00, so dinner can be the same table. "
             "Held 15 min. 18+, cashless."),
            ("~19:30", "go", "Shoreditch High Street → London Bridge, about 20 min", "Pack tonight: checkout and the York train tomorrow."),
        ],
        bookings=[
            ("Boundary Rooftop, Indoor Dining", "Sun 11 Oct, 17:30, 2 guests", "boundary"),
        ],
        notes=["Three years and eleven months today."],
    ),
    dict(
        n=9, slug="day09-mon-12-oct", dow="Monday", date="12 October", city="London → York",
        title="North to York",
        stay=("Travelodge York Central Micklegate", "Micklegate, YO1 6JG",
              "Twin room booked; ask at the desk for a double. Room only, no breakfast."),
        anchors=[("12:00", "Check out"), ("12:33", "LNER to York"), ("19:15", "Rustique")],
        timeline=[
            ("11:45", "key", "Check out of Premier Inn Southwark (deadline 12:00)", "Check the room twice."),
            ("11:50", "go", "Borough → King's Cross St Pancras, about 20 min",
             "Borough station, 2 min from the door. Northern line northbound, Bank branch, 6 stops, no change."),
            ("12:33", "key", "LNER King's Cross → York, arrives 14:26",
             "Coach B, seats 21 and 22. Advance singles: valid on this train only."),
            ("14:26", "go", "York station → hotel, about 10 min walk", "Straight up Micklegate. Check in from 15:00."),
            ("15:20", "do", "The Shambles and the snickelways",
             "Down Micklegate, over Ouse Bridge, up Parliament St, about 12 min. York Ghost Merchants at 6 Shambles if the queue is short (closes 17:30)."),
            ("15:30", "opt", "Swap: The Cat's Whiskers, 46 Goodramgate",
             "Monday is the only slot (closed Tuesdays), about £8–10 each for an hour. It replaces the Ghost Merchants queue."),
            ("16:15", "eat", "Roberto gelato, 3 Goodramgate", "Shuts at 17:00."),
            ("16:45", "do", "Dean's Park, Minster Yard", "The quiet lawn against the Minster's north wall. 15 min."),
            ("17:05", "do", "Museum Gardens and St Mary's Abbey", "Gates close 18:00; head out of the bottom gate about 17:45."),
            ("17:45", "go", "Along the Ouse back to Micklegate, 20 min", ""),
            ("19:15", "eat", "Dinner: Rustique, booked 19:15–21:00", "28 Castlegate, 10 min from the hotel. French bistro."),
            ("21:15", "opt", "Nightcap: The Falcon Tap, 94 Micklegate", "30 seconds from the door, closes 22:00."),
        ],
        bookings=[
            ("LNER King's Cross → York", "Mon 12 Oct, 12:33 → 14:26, Coach B 21 & 22", "lner1"),
            ("Travelodge York Central Micklegate, 2 nights", "12 → 14 Oct", "tlyork"),
            ("Rustique", "Mon 12 Oct, 19:15–21:00, 2 people", "rustique"),
        ],
        notes=["Monk Bar Chocolatiers is shut today; it's tomorrow."],
    ),
    dict(
        n=10, slug="day10-tue-13-oct", dow="Tuesday", date="13 October", city="York",
        title="All of York, on foot",
        stay=("Travelodge York Central Micklegate", "Micklegate, YO1 6JG", None),
        anchors=[("14:30", "Cocoa Works"), ("17:45", "Ambiente"), ("20:00", "Ghost Walk")],
        timeline=[
            ("09:30", "eat", "Breakfast: Partisan, 112 Micklegate",
             "2 min down the street. If the wait is over 15 min, try the Bar Convent café (17 Blossom St). For just coffee and a pastry, Spring Espresso (21 Lendal)."),
            ("10:25", "do", "The browsing morning, about 2 hrs",
             "Over Ouse Bridge → The Vintage Works, 8 Grape Lane (opens 10:30) → The Antiques Centre, 41 Stonegate → Stonegate → "
             "out through Bootham Bar → Gillygate: Blue Balloon, Rebound."),
            ("", "opt", "York Minster, optional", "About £20. The Great East Window and the Undercroft. Tower tickets are sold at the desk only."),
            ("12:50", "do", "City walls: Bootham Bar → Monk Bar",
             "The stairs are inside Bootham Bar. About 15 min, looking down on the Minster's east front."),
            ("13:10", "do", "Goodramgate charity shops, down to the Shambles", "RSPCA, Oxfam, BHF, Sue Ryder, Mind."),
            ("", "eat", "Monk Bar Chocolatiers, 7 Shambles", "The molten chocolate shot. Today is the only day it's open."),
            ("13:40", "eat", "Lunch: Shambles Market street-food row", "£6–10 a plate. Leave about 14:05."),
            ("14:05", "go", "Down Coppergate to Castlegate, 10 min", ""),
            ("14:30", "key", "York Cocoa Works bar-making workshop, 14:30–15:45",
             "10 Castlegate, YO1 9RN. Tell the guide about any allergy. The bar sets for about 30 min, so you'll leave around 16:15. 10% off in the shop."),
            ("16:15", "eat", "Luxury Ice Cream Company, Swinegate", "Then back to the hotel with your feet up."),
            ("17:30", "go", "Hotel → Fossgate, 15 min", ""),
            ("17:45", "eat", "Dinner: Ambiente Tapas, booked 17:45–19:30",
             "31 Fossgate, the Fossgate branch, not Goodramgate. Pay by about 19:45."),
            ("20:00", "key", "The Original Ghost Walk of York",
             "Meets outside The King's Arms, King's Staith (the bottom of Ouse Bridge). £10 each, cash. No booking. About 80 min; ends near the Minster about 21:20."),
            ("21:20", "go", "Walk home: Stonegate → St Helen's Sq → Ouse Bridge → Micklegate, 20 min", "Bring the hoods."),
        ],
        bookings=[
            ("York Cocoa Works, 2 adults", "Tue 13 Oct, 14:30–15:45", "cocoa"),
            ("Ambiente Tapas, Fossgate", "Tue 13 Oct, 17:45–19:30, 2 guests", "ambiente"),
        ],
        notes=["Wet day: skip Gillygate and the wall; take the Merchant Adventurers' Hall (Fossgate, about £8), then JORVIK or the Castle Museum near Castlegate.",
               "Bring £20 in cash for the ghost walk."],
    ),
    dict(
        n=11, slug="day11-wed-14-oct", dow="Wednesday", date="14 October", city="York → Edinburgh",
        title="Bettys, the coast train, and Calton Hill",
        stay=("Travelodge Edinburgh Central", "33 St Mary's Street, EH1 1TA",
              "Breakfast prepaid for both of you, both mornings."),
        anchors=[("12:19", "LNER to Edinburgh"), ("18:15", "Calton Hill"), ("19:30", "Devil's Advocate")],
        timeline=[
            ("09:35", "go", "Hotel → St Helen's Square, 10 min", "Leave the bags in the room."),
            ("09:45", "eat", "Breakfast: Bettys, 6–8 St Helen's Square",
             "No bookings. If the queue has started, Little Bettys at 46 Stonegate (sit upstairs)."),
            ("10:50", "do", "Stonegate on the way back", "Last of the shopping."),
            ("By 11:35", "key", "Check out of the Travelodge (deadline 12:00)",
             "Optional: Micklegate Bar stairs → the short stretch of wall toward Barker Tower, 10 min round trip."),
            ("11:45", "go", "Down Micklegate to the station", ""),
            ("12:19", "key", "LNER York → Edinburgh Waverley, arrives 14:39",
             "Coach G, seats 13 and 14, right-hand side. Advance singles, this train only. Durham about 45 min in; the coast from Alnmouth; then Bamburgh and Berwick."),
            ("14:39", "do", "At Waverley: ask at left luggage about Friday",
             "Opening time, price, and whether they take 20 kg cases."),
            ("14:50", "go", "Waverley → hotel, 10 min uphill",
             "Market Street exit → Cockburn Street → turn right on the High Street → St Mary's Street is on the right at the Netherbow. Taxi rank on Waverley Bridge, about £8."),
            ("15:10", "do", "Check in, drop everything", "Check-in from 15:00."),
            ("15:40", "opt", "Dean Village, 30 min walk",
             "Down the Mound → Princes St → Queensferry St → Bells Brae. Skip it if you leave after 15:45."),
            ("16:30", "opt", "Water of Leith Walkway → Stockbridge, 25 min",
             "Cake at Books N' Cup, 16 Raeburn Place; then Circus Lane."),
            ("17:45", "go", "Bus 24 or 29 → east end of Princes St, 10 min", "£2.40, tap contactless."),
            ("18:15", "do", "Calton Hill at sunset",
             "Steps off Waterloo Place. Dugald Stewart Monument for the view. The best half hour is just after sunset. Wear your warmest coat."),
            ("19:30", "eat", "Dinner: The Devil's Advocate, booked 19:30–21:30",
             "9 Advocate's Close, off the Royal Mile. Held 15 min. A cancellation or no-show inside 48 hrs is £10pp."),
        ],
        bookings=[
            ("LNER York → Edinburgh", "Wed 14 Oct, 12:19 → 14:39, Coach G 13 & 14", "lner2"),
            ("Travelodge Edinburgh Central, 2 nights", "14 → 16 Oct", "tledi"),
            ("The Devil's Advocate", "Wed 14 Oct, 19:30–21:30, 2 people", "devils"),
        ],
        notes=["Generate a fresh UKVI share code today or tomorrow for the Cork folder. Write it down."],
    ),
    dict(
        n=12, slug="day12-thu-15-oct", dow="Thursday", date="15 October", city="Edinburgh",
        title="Arthur's Seat, the oldest pub in Scotland, and a secret garden",
        stay=("Travelodge Edinburgh Central", "33 St Mary's Street, EH1 1TA", None),
        anchors=[("10:30", "Holyrood gate"), ("13:30", "Sheep Heid Inn"), ("19:00", "Angels with Bagpipes")],
        timeline=[
            ("09:00", "eat", "Prepaid breakfast at the Travelodge, 09:00–09:45", "The one lie-in of the fortnight."),
            ("10:15", "go", "Down the Canongate to the Holyrood gate, 15 min",
             "Fill water bottles and put coats on. There are no shops in the park."),
            ("10:30", "do", "Arthur's Seat, summit route",
             "About 75 min up (rough steps at the top), 20 min on top, 40 min down the east side to Duddingston. "
             "Flat alternative: the low path round the south side, about 40 min. Pick at the gate."),
            ("12:45", "do", "Reach Duddingston", "45 minutes in hand. On the flat route, do Dr Neil's Garden before lunch."),
            ("13:30", "eat", "Lunch: The Sheep Heid Inn, booked",
             "43–45 The Causeway, EH15 3QA. Restaurant area. Held 15 min only, so 13:45 is the deadline."),
            ("~14:45", "do", "Dr Neil's Garden, Old Church Lane", "Free. Go via the Duddingston Kirk car park; the gate sticks, so shove it."),
            ("16:00", "go", "Lothian bus 12 from Duddingston Road West, about 25 min", "£2.40 contactless. (Not the 42.)"),
            ("16:30", "key", "At the hotel: weigh her bag",
             "The Ryanair allowance is 20 kg. Stand on the bathroom scale with and without the bag. If it's over, buy extra weight online tonight."),
            ("", "do", "If Waverley left luggage didn't suit, ask the Travelodge desk to hold the bags tomorrow until about 17:00", ""),
            ("19:00", "eat", "Dinner: Angels with Bagpipes, booked",
             "343 High Street, 5 min from the hotel. Kitchen to 21:15."),
            ("20:45", "opt", "One drink: Hoot the Redeemer, 7 Hanover St", "Unmarked red door. Skip it without guilt."),
        ],
        bookings=[
            ("The Sheep Heid Inn", "Thu 15 Oct, 13:30, 2 people, Restaurant", "sheep"),
            ("Angels with Bagpipes", "Thu 15 Oct, 19:00, 2 people", "angels"),
        ],
        notes=["Rain: take the flat path round the base. The Palace of Holyroodhouse (about £20) is the indoor fallback."],
    ),
    dict(
        n=13, slug="day13-fri-16-oct", dow="Friday", date="16 October", city="Edinburgh → Airport",
        title="The Old Town, then out to the airport hotel",
        stay=("Moxy Edinburgh Airport", "1 Fairview Road, EH28 8AP",
              "No shuttle. About 800 yds from the terminal. No breakfast included."),
        anchors=[("10:00", "Castle"), ("13:50", "Mary King's Close check-in"), ("17:25", "Tram"),
                 ("19:00", "Folder hour")],
        timeline=[
            ("08:45", "key", "Check out; bags to Waverley left luggage (or the Travelodge desk)",
             "No suitcases or rucksacks over 30 L are allowed at the Castle."),
            ("~09:40", "go", "Up the Royal Mile to the Castle, 15 min", ""),
            ("10:00", "key", "Edinburgh Castle, entry 10:00–10:30",
             "St Margaret's Chapel, the Honours of Scotland, Mons Meg and the Great Hall, the National War Memorial (no photos), the north battlements. 2–2.5 hrs."),
            ("12:00", "do", "Victoria Street → Victoria Terrace → the Grassmarket", "Go up onto the terrace for the photo."),
            ("12:30", "eat", "Lunch in the Grassmarket, walk-in",
             "Petit Paris (38–40) or Maison Bleue, Biddy Mulligans, The Last Drop. The One O'Clock Gun fires at 13:00."),
            ("13:35", "go", "Leave the Grassmarket, 10 min up to St Giles'", ""),
            ("13:50", "key", "Check in: The Real Mary King's Close, tour 14:00",
             "2 Warriston's Close, on the Royal Mile opposite St Giles'. About an hour, cold and enclosed. Out about 15:05."),
            ("15:30", "opt", "Maison de Moggy cat café, 17–19 West Port",
             "Walk-up, from £12 each, hourly slots. Shoes off. If it's full: the National Museum of Scotland (free, 7 min) or Armchair Books next door."),
            ("16:30", "eat", "Mary's Milk Bar, 19 Grassmarket",
             "Hot chocolate float. Buy a box of chocolates for tonight."),
            ("16:55", "go", "Grassmarket → Waverley (15 min), collect the bags → St Andrew Square (5 min)", ""),
            ("17:25", "key", "Tram to Ingliston Park & Ride, about 28 min",
             "Buy a City single (£2.40) before boarding. Get off one stop before the airport, then walk about 10 min / 0.4 mi to the Moxy. "
             "If it's pouring, ride to the airport instead (about £8)."),
            ("~18:15", "do", "Check in at the Moxy", "Free drink at check-in; Bar Moxy does food all night."),
            ("19:00", "key", "The folder hour: check the Cork folder, all of it in hand luggage",
             "BMU email on top · FR3732 itinerary + Manila–Heathrow booking · the Southwark, York and Edinburgh hotel confirmations · "
             "fresh UKVI share code + eVisa on the phone and as a PDF · the Irish SSVWP page · the January flight, Simon's letter, passport copy, funds, insurance."),
            ("", "key", "Check both boarding passes in the Ryanair app and screenshot them onto both phones",
             "A restricted pass for Jenifer is normal: her document is checked at the bag drop. Don't pay the airport check-in fee."),
            ("21:00", "do", "Chocolates, the telly, phones on charge, both alarms at 04:15", "Bags by the door."),
        ],
        bookings=[
            ("Edinburgh Castle, 2 adults", "Fri 16 Oct, entry 10:00–10:30", "hes"),
            ("The Real Mary King's Close, 2 adults", "Fri 16 Oct, 14:00 tour, check in 13:50", "mkc"),
            ("Moxy Edinburgh Airport, 1 night", "16 → 17 Oct, Queen Sleeper", "moxy"),
        ],
        notes=[],
    ),
    dict(
        n=14, slug="day14-sat-17-oct", dow="Saturday", date="17 October", city="Edinburgh → Cork",
        title="FR3732 to Cork, and the Irish border",
        stay=("Home: Blarney, Co. Cork", "About 25 min by car from Cork Airport", None),
        anchors=[("04:15", "Alarm"), ("06:25", "Bag drop closes"), ("07:05", "FR3732"), ("08:25", "Land Cork")],
        timeline=[
            ("04:15", "key", "Alarm", "Bags were packed last night and the folder is in hand luggage."),
            ("04:30", "go", "Walk to the terminal, about 10 min", "800 yds, across one road."),
            ("04:45", "key", "Ryanair bag drop (closes 06:25)",
             "Two 20 kg bags. Jenifer's document is checked here if her pass is restricted. Have the Irish SSVWP notice and the BMU email out."),
            ("05:15", "do", "Security", "Breakfast airside."),
            ("06:30", "do", "Gate", "Sunrise isn't until about 07:45. Sleep on the flight."),
            ("07:05", "key", "FR3732 Edinburgh → Cork, 1 hr 20 min", "Seats 02B (Simon) and 02C (Jenifer)."),
            ("08:25", "key", "Land at Cork → immigration",
             "Simon goes to the desk with her. Entry under the Short Stay Visa Waiver Programme. Give the January departure date and put the onward ticket on the counter. "
             "A supervisor check is normal. Check the stamp is legible before you walk away."),
            ("~09:15", "go", "Car to Blarney, about 25 min", "Nothing to book."),
        ],
        bookings=[
            ("Ryanair FR3732, both travellers", "Sat 17 Oct, 07:05 EDI → 08:25 ORK", "ryanair"),
        ],
        notes=["If FR3732 is cancelled, fly Edinburgh → Dublin (several flights a day), then the train Heuston → Cork, about 2.5 hrs. "
               "The BMU accepts Dublin in writing. The entry deadline is 31 Oct.",
               "The full border brief is on the borders page."],
    ),
]

KIND_LABEL = {"go": "Travel", "eat": "Eat", "do": "", "opt": "Optional", "key": ""}

CSS = """
@page { size: A4; margin: 9mm 11mm 9mm 11mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 9pt; line-height: 1.28; color: #1a1a1a; margin: 0; }
.head { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2.5pt solid #1f3a5f; padding-bottom: 5pt; }
.day { font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; color: #1f3a5f; font-weight: 700; }
h1 { font-size: 19pt; margin: 1pt 0 0; line-height: 1.1; }
.title { font-size: 11pt; color: #444; margin-top: 2pt; }
.city { text-align: right; font-size: 10.5pt; font-weight: 700; color: #1f3a5f; }
.stay { margin-top: 6pt; padding: 5pt 8pt; background: #eef2f7; border-left: 3pt solid #1f3a5f; font-size: 9pt; }
.stay b { font-size: 9.6pt; }
.anchors { display: flex; flex-wrap: wrap; gap: 4pt; margin: 6pt 0 4pt; }
.chip { border: 1pt solid #1f3a5f; border-radius: 3pt; padding: 2pt 6pt; font-size: 8.8pt; }
.chip b { color: #1f3a5f; }
h2 { break-after: avoid; page-break-after: avoid; font-size: 9.5pt; text-transform: uppercase; letter-spacing: .07em; color: #1f3a5f; margin: 7pt 0 3pt; border-bottom: .75pt solid #b8c4d4; padding-bottom: 1.5pt; }
table.tl { width: 100%; border-collapse: collapse; }
table.tl td { vertical-align: top; padding: 2.3pt 4pt; border-bottom: .5pt solid #dde3ea; }
table.tl tr { page-break-inside: avoid; break-inside: avoid; }
td.t { width: 15mm; font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
td.w b { font-weight: 650; }
.d { color: #3a3a3a; font-size: 8.8pt; }
.tag { display: inline-block; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; border-radius: 2pt; padding: 0 3pt; margin-right: 4pt; vertical-align: 1pt; }
tr.go td.w b { font-style: italic; font-weight: 600; }
tr.go .tag { background: #e3e8ef; color: #1f3a5f; }
tr.eat .tag { background: #f3e9d9; color: #7a4a0c; }
tr.opt .tag { background: #fff; color: #666; border: .6pt dashed #888; }
tr.opt td { color: #555; }
tr.key td.t { color: #fff; background: #1f3a5f; }
tr.key td.w { background: #f4f6f9; }
.check { display: inline-block; width: 8pt; height: 8pt; border: .8pt solid #555; margin-right: 4pt; vertical-align: -1pt; }
.bk { display: grid; grid-template-columns: 1fr 1fr; gap: 5pt; }
.card { border: .9pt solid #9aa9bd; border-radius: 3pt; padding: 4pt 5pt; break-inside: avoid; page-break-inside: avoid; }
.card .nm { font-weight: 700; font-size: 9.5pt; }
.card .when { font-size: 8.6pt; color: #333; margin-bottom: 2pt; }
.mail { font-size: 8.2pt; color: #333; margin-top: 3pt; border-top: .5pt dotted #aaa; padding-top: 2pt; overflow-wrap: anywhere; }
.mail i { color: #000; }
.notes { margin: 3pt 0 0; padding-left: 14pt; font-size: 8.6pt; }
.notes li { margin-bottom: 2pt; }
.foot { margin-top: 5pt; font-size: 7.5pt; color: #777; border-top: .5pt solid #ccc; padding-top: 3pt; }
"""


def esc(s):
    return html.escape(s or "")


def render(day):
    stay_name, stay_addr, stay_note = day["stay"]
    parts = [f"<!doctype html><html><head><meta charset='utf-8'><title>Day {day['n']} · {esc(day['dow'])} {esc(day['date'])}</title>"
             f"<style>{CSS}</style></head><body>"]
    parts.append(
        f"<div class='head'><div><div class='day'>Day {day['n']} of 14 · {esc(day['dow'])}</div>"
        f"<h1>{esc(day['dow'])} {esc(day['date'])} 2026</h1><div class='title'>{esc(day['title'])}</div></div>"
        f"<div class='city'>{esc(day['city'])}</div></div>")
    note = f"<br>{esc(stay_note)}" if stay_note else ""
    parts.append(f"<div class='stay'>Tonight: <b>{esc(stay_name)}</b> · {esc(stay_addr)}{note}</div>")
    parts.append("<div class='anchors'>" + "".join(
        f"<span class='chip'><b>{esc(t)}</b> {esc(w)}</span>" for t, w in day["anchors"]) + "</div>")

    parts.append("<h2>The day</h2><table class='tl'>")
    for t, kind, what, detail in day["timeline"]:
        tag = KIND_LABEL[kind]
        tag_html = f"<span class='tag'>{tag}</span>" if tag else ""
        box = "<span class='check'></span>" if kind == "key" else ""
        det = f"<div class='d'>{esc(detail)}</div>" if detail else ""
        parts.append(f"<tr class='{kind}'><td class='t'>{esc(t)}</td>"
                     f"<td class='w'>{box}{tag_html}<b>{esc(what)}</b>{det}</td></tr>")
    parts.append("</table>")

    parts.append("<h2>Bookings: find the email</h2><div class='bk'>")
    for name, when, ekey in day["bookings"]:
        if ekey:
            subj, sender, date = EMAILS[ekey]
            mail = (f"<div class='mail'>Email: <b>“{esc(subj)}”</b><br>from {esc(sender)}, received {esc(date)}</div>")
        else:
            mail = "<div class='mail'>No confirmation email yet.</div>"
        parts.append(f"<div class='card'><div class='nm'>{esc(name)}</div>"
                     f"<div class='when'>{esc(when)}</div>{mail}</div>")
    parts.append("</div>")

    if day["notes"]:
        parts.append("<h2>Notes</h2><ul class='notes'>" + "".join(f"<li>{esc(n)}</li>" for n in day["notes"]) + "</ul>")
    parts.append("<div class='foot'>Simon &amp; Jenifer · UK, 4–17 October 2026 · Filled boxes are fixed times. "
                 "Emails are in Simon's Gmail; times are when they arrived (Irish time).</div>")
    parts.append("</body></html>")
    return "".join(parts)


def browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    sys.exit("No Chrome or Edge found")


def main():
    only = set(sys.argv[1:])
    os.makedirs(OUT_HTML, exist_ok=True)
    os.makedirs(OUT_PDF, exist_ok=True)
    exe = browser()
    for day in DAYS:
        if only and day["slug"] not in only and str(day["n"]) not in only:
            continue
        h = os.path.join(OUT_HTML, day["slug"] + ".html")
        p = os.path.join(OUT_PDF, day["slug"] + ".pdf")
        with open(h, "w", encoding="utf-8") as f:
            f.write(render(day))
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={p}", "file:///" + h.replace("\\", "/")],
                       check=True, capture_output=True)
        print(p)

    import pypdf
    writer = pypdf.PdfWriter()
    for day in DAYS:
        writer.append(os.path.join(OUT_PDF, day["slug"] + ".pdf"))
    master = os.path.join(OUT_PDF, "all-days.pdf")
    writer.write(master)
    print(master)


if __name__ == "__main__":
    main()
