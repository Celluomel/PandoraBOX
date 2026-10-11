from math import atan2, cos, pi, sin
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "ventuno_sensor_chassis_cardboard_mockup_a4.pdf"
SCAD = ROOT / "docs" / "hardware" / "hexapode_chassis_ventuno_q_light.scad"
PAGE = landscape(A4)
PW, PH = PAGE
RED = colors.HexColor("#c0392b")
BLUE = colors.HexColor("#1878a5")
INK = colors.HexColor("#203238")
GRAY = colors.HexColor("#66777c")
GREEN = colors.HexColor("#14866d")


def header(c, title, subtitle):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(15 * mm, PH - 15 * mm, title)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8.5)
    c.drawString(15 * mm, PH - 21 * mm, subtitle)
    c.setStrokeColor(colors.HexColor("#d6e0e2"))
    c.line(15 * mm, PH - 24 * mm, PW - 15 * mm, PH - 24 * mm)


def footer(c, page, note="Print at 100% / Actual size. Disable Fit to page."):
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(15 * mm, 8 * mm, note)
    c.drawRightString(PW - 15 * mm, 8 * mm, f"PandoraBOX mockup | A4 | {page}")


def path_poly(c, pts, x0, y0, scale=mm, stroke=RED, fill=None, close=True, width=0.55):
    p = c.beginPath()
    p.moveTo(x0 + pts[0][0] * scale, y0 + pts[0][1] * scale)
    for x, y in pts[1:]:
        p.lineTo(x0 + x * scale, y0 + y * scale)
    if close:
        p.close()
    c.setStrokeColor(stroke)
    c.setLineWidth(width)
    if fill:
        c.setFillColor(fill)
    c.drawPath(p, stroke=1, fill=1 if fill else 0)


def circle(c, x, y, d, x0, y0, stroke=BLUE, dashed=True, label=None):
    c.saveState()
    c.setStrokeColor(stroke)
    c.setLineWidth(0.45)
    if dashed:
        c.setDash(2, 1.5)
    c.circle(x0 + x * mm, y0 + y * mm, d * mm / 2, stroke=1, fill=0)
    c.setDash()
    if label:
        c.setFont("Helvetica", 5.5)
        c.setFillColor(stroke)
        c.drawCentredString(x0 + x * mm, y0 + y * mm - 1.8 * mm, label)
    c.restoreState()


def slot(c, x, y, sx, sy, r, x0, y0):
    c.setStrokeColor(RED)
    c.setLineWidth(0.45)
    c.roundRect(x0 + (x - sx / 2) * mm, y0 + (y - sy / 2) * mm,
                sx * mm, sy * mm, r * mm, stroke=1, fill=0)


def dashed_line(c, x1, y1, x2, y2, x0, y0, color=BLUE):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(0.45)
    c.setDash(2, 1.5)
    c.line(x0 + x1 * mm, y0 + y1 * mm, x0 + x2 * mm, y0 + y2 * mm)
    c.restoreState()


def calibration_box(c, x, y):
    c.setStrokeColor(INK)
    c.setLineWidth(0.65)
    c.rect(x, y, 50 * mm, 50 * mm, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + 25 * mm, y + 25 * mm, "50 mm CHECK")


def deck_outline(section):
    if section == "front":
        return [(-80, 25), (80, 25), (80, 95), (0, 115), (-80, 95)]
    if section == "center":
        return [(-80, -25), (80, -25), (80, 25), (-80, 25)]
    return [(-80, -25), (80, -25), (80, -95), (36, -115), (-36, -115), (-80, -95)]


def piece_page(c, deck, section, page):
    title = f"{deck.upper()} DECK - {section.upper()} SECTION"
    header(c, title, "Full scale 1:1 template. Cut the red outline and openings; pierce the blue fastener marks.")
    pts = deck_outline(section)
    minx = min(x for x, _ in pts)
    miny = min(y for _, y in pts)
    maxx = max(x for x, _ in pts)
    maxy = max(y for _, y in pts)
    x0 = 23 * mm - minx * mm
    y0 = (PH - 24 * mm - (maxy - miny) * mm) / 2 - miny * mm
    path_poly(c, pts, x0, y0)
    ylo, yhi = {"front": (25, 115), "center": (-25, 25), "rear": (-115, -25)}[section]

    if deck == "lower":
        for sy in (-63, 0, 63):
            if ylo <= sy <= yhi:
                for side in (-1, 1):
                    # Servo windows are square-cornered cuts in the STL.
                    c.setStrokeColor(RED)
                    c.setLineWidth(0.45)
                    c.rect(x0 + (58 if side > 0 else -81) * mm,
                           y0 + (sy - 20.25) * mm, 23 * mm, 40.5 * mm, stroke=1, fill=0)
                    hx = side * 68.25
                    for hy in (sy - 24.75, sy + 24.75):
                        if ylo - 2 <= hy <= yhi + 2:
                            circle(c, hx, hy, 4, x0, y0, label="4")
        for x in (-36, -12, 12, 36):
            for y in (-55, 55):
                if ylo - 10 <= y <= yhi + 10:
                    slot(c, x, y, 14, 20, 4, x0, y0)
        for x, y in ((-45, -75), (45, -75), (-45, 75), (45, 75)):
            if ylo <= y <= yhi:
                circle(c, x, y, 3.2, x0, y0)
        for x in (-54, 54):
            for y in (-88, 0, 88):
                if ylo <= y <= yhi:
                    circle(c, x, y, 3.4, x0, y0)
        if section == "center":
            # Central cable pass-through.
            c.setStrokeColor(RED)
            c.rect(x0 - 20 * mm, y0 - 8 * mm, 40 * mm, 16 * mm, stroke=1, fill=0)
        for x in (-48, 0, 48):
            for seam in (-25, 25):
                yy = seam + (-8 if seam > 0 else 8)
                if ylo <= yy <= yhi:
                    circle(c, x, yy, 3.3, x0, y0, stroke=GREEN)
    else:
        for x in (-54, 54):
            for y in (-88, 0, 88):
                if ylo <= y <= yhi:
                    circle(c, x, y, 3.4, x0, y0)
        for x in (-50, 0, 50):
            for seam in (-25, 25):
                yy = seam + (-8 if seam > 0 else 8)
                if ylo <= yy <= yhi:
                    circle(c, x, yy, 3.3, x0, y0, stroke=GREEN)
        # Mount holes around lidar mast and central cable opening.
        for deg in (45, 135, 225, 315):
            circle(c, 20 * cos(deg * pi / 180), 20 * sin(deg * pi / 180), 3.2, x0, y0)
        if section == "center":
            circle(c, 0, 0, 16, x0, y0, stroke=RED, dashed=False)
            for x in (-7.5, 7.5):
                for y in (-6, 6):
                    circle(c, x, y - 42, 3.2, x0, y0)
        # Radar at y=58.
        if ylo <= 58 <= yhi:
            for x in (-26, 26):
                for y in (53.5, 38.5):
                    circle(c, x, y, 3.2, x0, y0)
        # ToF cradle at y=82.
        if ylo <= 82 <= yhi:
            for x in (-17, 17):
                circle(c, x, 75, 3.2, x0, y0)
        # GPS mount near the rear.
        if ylo <= -80 <= yhi:
            for x in (-9, 9):
                for y in (-89, -71):
                    circle(c, x, y, 3.2, x0, y0)
        # Three ultrasonic holder footprints (two front, one rear).
        a = atan2(20, 80)
        for tx, ty, angle in ((46, 95, -a), (-46, 95, a), (0, -115, pi)):
            if ylo - 16 <= ty <= yhi + 16:
                for sx in (-13, 13):
                    lx, ly = sx, -7
                    hx = tx + lx * cos(angle) - ly * sin(angle)
                    hy = ty + lx * sin(angle) + ly * cos(angle)
                    circle(c, hx, hy, 3.2, x0, y0)

    # A compact side legend and dimension labels.
    info_x = 218 * mm
    info_y = PH - 42 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(info_x, info_y, "CUT / ASSEMBLY")
    c.setFont("Helvetica", 8)
    c.setFillColor(RED)
    c.drawString(info_x, info_y - 7 * mm, "Red: cut line / opening")
    c.setFillColor(BLUE)
    c.drawString(info_x, info_y - 13 * mm, "Blue dashed: drill/pierce")
    c.setFillColor(GREEN)
    c.drawString(info_x, info_y - 19 * mm, "Green: splice strap holes")
    c.setFillColor(INK)
    c.drawString(info_x, info_y - 30 * mm, f"Envelope: {maxx-minx:.0f} x {maxy-miny:.0f} mm")
    c.drawString(info_x, info_y - 36 * mm, "Part thickness: 3.5 mm")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    c.drawString(info_x, info_y - 48 * mm, "Holes near a seam may form")
    c.drawString(info_x, info_y - 53 * mm, "an edge notch; use the straps")
    c.drawString(info_x, info_y - 58 * mm, "to bridge the joint underneath.")
    # Exact 50 mm calibration box.
    c.setStrokeColor(INK)
    c.setLineWidth(0.65)
    c.rect(info_x, 28 * mm, 50 * mm, 50 * mm, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(info_x + 25 * mm, 53 * mm, "50 mm CHECK")
    footer(c, page)
    c.showPage()


def overview_page(c):
    header(c, "CARDBOARD MOCKUP - SENSOR CHASSIS", "A4 print pack for a quick physical fit check of the VENTUNO Q sensor carrier. Templates are full size unless marked schematic.")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(18 * mm, PH - 35 * mm, "Exploded arrangement (schematic, not to scale)")

    # Top deck sketch and label.
    sx, sy = 0.38, 0.38
    cx, cy = 54 * mm, 121 * mm
    outline = [(0,115),(80,95),(80,-95),(36,-115),(-36,-115),(-80,-95),(-80,95)]
    path_poly(c, outline, cx, cy, scale=mm*sx, stroke=GREEN, width=1.0)
    def px(x): return cx + x * mm * sx
    def py(y): return cy + y * mm * sy
    c.setStrokeColor(GRAY); c.setDash(2,2)
    for x,y in ((0,0),(-54,-88),(54,-88),(-54,0),(54,0),(-54,88),(54,88)):
        c.circle(px(x),py(y),1.5*mm,stroke=1,fill=0)
    c.setDash()
    for x,y,label in ((0,0,"LIDAR"),(0,-42,"IMU"),(0,-80,"GPS"),(0,82,"ToF"),(0,58,"LD2450"),(-46,95,"US"),(46,95,"US"),(0,-115,"US")):
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(px(x),py(y)+2*mm,label)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx, 65*mm, "UPPER DECK / sensors face outward")

    # Lower deck and board/servo sketch.
    bx, by = 145 * mm, 121 * mm
    path_poly(c, outline, bx, by, scale=mm*sx, stroke=GREEN, width=1.0)
    def qx(x): return bx + x * mm * sx
    def qy(y): return by + y * mm * sy
    c.setFillColor(colors.HexColor("#dce7e8")); c.setStrokeColor(GRAY)
    c.rect(qx(-50),qy(-80),100*mm*sx,160*mm*sy,stroke=1,fill=1)
    c.setFillColor(INK); c.setFont("Helvetica-Bold",6)
    c.drawCentredString(qx(0),qy(0),"VENTUNO Q")
    for yy in (-63,0,63):
        for side in (-1,1):
            c.setStrokeColor(RED)
            c.rect(qx(side*69.5-6.5),qy(yy-11.5),13*mm*sx,23*mm*sy,stroke=1,fill=0)
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8)
    c.drawCentredString(bx,65*mm,"LOWER DECK / board and servo lands")

    # Side view.
    c.setFillColor(INK); c.setFont("Helvetica-Bold",10)
    c.drawString(18*mm, 53*mm, "Side stack")
    c.setStrokeColor(GREEN); c.setLineWidth(2)
    c.line(25*mm,31*mm,96*mm,31*mm)
    c.line(25*mm,45*mm,96*mm,45*mm)
    c.setStrokeColor(BLUE); c.setLineWidth(1)
    for x in (34,50,66,82,98,112):
        c.line(x*mm,31*mm,x*mm,45*mm)
    c.setFillColor(GRAY); c.setFont("Helvetica",8)
    c.drawString(101*mm,43*mm,"Upper deck 3.5 mm")
    c.drawString(101*mm,37*mm,"55 mm spacer gap")
    c.drawString(101*mm,30*mm,"Lower deck 3.5 mm")

    # Printable instructions at right.
    ix, iy = 193*mm, 83*mm
    c.setFillColor(INK); c.setFont("Helvetica-Bold",10)
    c.drawString(ix,iy,"Print and assemble")
    instructions = [
        "1. Print pages 2-11 at Actual size, landscape A4.",
        "2. Measure the 50 mm check box before cutting.",
        "3. Cut six deck panels; tape the seams from below.",
        "4. Use splice marks and sensor footprints as guides.",
        "5. Fold/roll the holder nets on pages 8-10.",
        "6. Make six 55 mm spacer tubes from page 11.",
        "7. Mockup only: cardboard is not load-bearing.",
    ]
    c.setFont("Helvetica",8)
    c.setFillColor(GRAY)
    for i,line in enumerate(instructions):
        c.drawString(ix,iy-(7+i*6)*mm,line)
    c.setFillColor(RED); c.setFont("Helvetica-Bold",8)
    c.drawString(18*mm,17*mm,"Warning: board-hole coordinates and sensor fit are provisional. Confirm against the actual modules before cutting the final cardboard pieces.")
    footer(c,1,"A4 landscape; template pages are 1:1. This mockup is for arrangement and clearance only.")
    c.showPage()


def net_base(c, x, y, w, d, wall_h, title, note, holes=()):
    # Fold-up holder net: bed footprint plus a connected rear wall and glue flaps.
    flap = 6
    total_w = w + 2*flap
    base_y = y
    c.setStrokeColor(RED); c.setLineWidth(0.6)
    c.rect(x,base_y,w*mm,d*mm,stroke=1,fill=0)
    c.rect(x,base_y+d*mm,w*mm,wall_h*mm,stroke=1,fill=0)
    # glue tabs either side of the back wall
    path_poly(c,[(0,0),(flap,5),(flap,wall_h-5),(0,wall_h)],x-flap*mm,base_y+d*mm,stroke=RED)
    path_poly(c,[(0,5),(flap,0),(flap,wall_h),(0,wall_h-5)],x+w*mm,base_y+d*mm,stroke=RED)
    dashed_line(c,0,d,w,d,x/mm,y/mm)
    c.setStrokeColor(BLUE); c.setDash(2,1.5)
    for hx,hy,hd in holes:
        c.circle(x+hx*mm,base_y+hy*mm,hd*mm/2,stroke=1,fill=0)
    c.setDash()
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8)
    c.drawString(x-flap*mm,base_y+(d+wall_h+8)*mm,title)
    c.setFillColor(GRAY); c.setFont("Helvetica",7)
    c.drawString(x-flap*mm,base_y-5*mm,note)
    c.setStrokeColor(BLUE); c.setDash(2,1.5)
    c.line(x,base_y+d*mm,x+w*mm,base_y+d*mm)
    c.setDash()


def holder_pages(c):
    # Page 8: front ultrasonic cradle nets, two per sheet and print 3 copies.
    header(c,"CARDBOARD HOLDERS - ULTRASONIC + RADAR","Fold lines are blue dashed. Red is cut. Approximate envelope/template from the current STL geometry.")
    for x,y in ((20*mm,125*mm),(110*mm,125*mm),(200*mm,125*mm)):
        net_base(c,x,y,60,14,26,"HC-SR04 cradle - make 3","Two 16.5 mm transducer holes; scale 1:1.",holes=((17,7,3.2),(43,7,3.2)))
        # transducer apertures are placed in the upright wall.
        c.setStrokeColor(RED); c.setLineWidth(0.55)
        c.circle(x+17*mm,y+(14+13)*mm,8.25*mm,stroke=1,fill=0)
        c.circle(x+43*mm,y+(14+13)*mm,8.25*mm,stroke=1,fill=0)
        c.rect(x+6.8*mm,y+14*mm,46.4*mm,21*mm,stroke=1,fill=0)
    c.setFillColor(GRAY); c.setFont("Helvetica",8)
    c.drawString(20*mm,105*mm,"Cut three copies. Add paper rings behind the apertures to represent the transducer barrels.")
    net_base(c,42*mm,22*mm,60,24,58,"LD2450 radar tower base + wall","Wall window 35.5 x 20.5 mm; leave it open for the mockup.",holes=((4,4,3.2),(56,4,3.2),(4,19.5,3.2),(56,19.5,3.2)))
    c.setStrokeColor(RED); c.rect(42*mm+12.25*mm,22*mm+24*mm+30*mm,35.5*mm,20.5*mm,stroke=1,fill=0)
    calibration_box(c, 230*mm, 22*mm)
    footer(c,8,"Cardboard holder nets approximate the STL shape; use tape at the tabs. Do not attach powered electronics to cardboard.")
    c.showPage()

    # Page 9: ToF, IMU and splice straps, all 1:1.
    header(c,"CARDBOARD HOLDERS - ToF / IMU / DECK JOINTS","Fold the ToF side walls upward; stack IMU pads; tape splice straps under the deck seams.")
    # ToF cradle: base plus separately glued side ears and rear retaining lip.
    c.setStrokeColor(RED); c.setLineWidth(0.6)
    c.rect(35*mm,106*mm,40*mm,24*mm,stroke=1,fill=0)
    for hx in (38*mm,72*mm):
        c.setStrokeColor(BLUE); c.setDash(2,1.5); c.circle(hx,110*mm,1.6*mm,stroke=1,fill=0); c.setDash()
    c.rect(35*mm,139*mm,23*mm,4*mm,stroke=1,fill=0)
    c.rect(52*mm,139*mm,23*mm,4*mm,stroke=1,fill=0)
    c.rect(80*mm,106*mm,36*mm,3*mm,stroke=1,fill=0)
    c.setFillColor(GRAY); c.setFont("Helvetica",6)
    c.drawString(35*mm,145*mm,"2 side ears 23 x 4; rear lip 36 x 3. Glue upright at marked base edges.")
    c.setFillColor(GRAY); c.setFont("Helvetica",7)
    c.drawString(35*mm,101*mm,"Glue/fold narrow rails into a U cradle. Leave the sensor lens end clear.")
    # IMU pad cut outline and holes
    x,y=116*mm,112*mm
    c.setStrokeColor(RED); c.rect(x,y,30*mm,26*mm,stroke=1,fill=0)
    for hx in (7.5,22.5):
        for hy in (7,19):
            c.setStrokeColor(BLUE); c.setDash(2,1.5); c.circle(x+hx*mm,y+hy*mm,1.6*mm,stroke=1,fill=0); c.setDash()
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8); c.drawString(x,y+31*mm,"IMU pad - stack 1 or 2 layers")
    # splice straps, six copies per deck
    for x,y in ((179*mm,127*mm),(207*mm,127*mm),(235*mm,127*mm),(179*mm,76*mm),(207*mm,76*mm),(235*mm,76*mm)):
        c.setStrokeColor(RED); c.rect(x,y,18*mm,32*mm,stroke=1,fill=0)
        for hy in (8,24):
            c.setStrokeColor(BLUE); c.setDash(2,1.5); c.circle(x+9*mm,y+hy*mm,1.65*mm,stroke=1,fill=0); c.setDash()
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8); c.drawString(179*mm,166*mm,"Deck splice strap 18 x 32 mm - cut 12")
    c.setFillColor(GRAY); c.setFont("Helvetica",7)
    c.drawString(179*mm,69*mm,"Tape 3 straps under each seam. M3 hardware belongs to the later rigid build.")
    calibration_box(c, 230*mm, 13*mm)
    footer(c,9,"Red solid = cut; blue dashed = pierce/fold. All templates on this page are 1:1.")
    c.showPage()

    # Page 10: round mast forms, GPS support and spacer tubes.
    header(c,"CARDBOARD HOLDERS - MASTS + SPACERS","Cut, roll, and tape paper forms to check heights and collisions. Dimensions are 1:1 except notes marked schematic.")
    # Lidar cylinder strip and circular plates.
    x,y=20*mm,100*mm
    c.setStrokeColor(RED); c.rect(x,y,115*mm,75*mm,stroke=1,fill=0)
    c.setStrokeColor(BLUE); c.setDash(2,1.5); c.line(x+107*mm,y,x+107*mm,y+75*mm); c.setDash()
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8); c.drawString(x,y+79*mm,"LIDAR mast - roll 34 mm diameter x 75 mm high")
    c.setFillColor(GRAY); c.setFont("Helvetica",7); c.drawString(x,y-5*mm,"Strip includes 8 mm glue flap; base circle dia 50 mm, top plate dia 72 mm.")
    # diameter circles drawn true size
    c.setStrokeColor(RED); c.circle(164*mm,50*mm,25*mm,stroke=1,fill=0)
    c.circle(226*mm,50*mm,36*mm,stroke=1,fill=0)
    c.setFillColor(INK); c.setFont("Helvetica",7); c.drawCentredString(164*mm,50*mm,"BASE 50")
    c.drawCentredString(226*mm,50*mm,"TOP 72")
    # GPS mast cross wrap 10x10x40 with flap
    x,y=20*mm,40*mm
    widths=[10,10,10,10,5]
    xx=x
    for w in widths:
        c.setStrokeColor(RED); c.rect(xx,y,w*mm,40*mm,stroke=1,fill=0)
        xx += w*mm
    for i in range(1,5):
        c.setStrokeColor(BLUE); c.setDash(2,1.5); c.line(x+sum(widths[:i])*mm,y,x+sum(widths[:i])*mm,y+40*mm); c.setDash()
    c.setFillColor(INK); c.setFont("Helvetica-Bold",8); c.drawString(x,y+44*mm,"GPS mast wrap: 10 x 10 x 40 mm")
    c.setFillColor(GRAY); c.setFont("Helvetica",7); c.drawString(x,y-5*mm,"Fold into square tube; glue the edge.")
    for x0,y0,d,label in ((70*mm,37*mm,26,"GPS BASE 26"),(100*mm,32*mm,36,"GPS TOP 36")):
        c.setStrokeColor(RED); c.rect(x0,y0,d*mm,d*mm,stroke=1,fill=0)
        c.setFillColor(INK); c.setFont("Helvetica",6.5); c.drawCentredString(x0+d*mm/2,y0+d*mm/2,label)
    calibration_box(c, 237*mm, 95*mm)
    footer(c,10,"Red solid = cut; blue dashed = fold/roll. Mast templates are visual mockups, not load-bearing parts.")
    c.showPage()

    # Page 11: spacer-tube strips.
    header(c,"CARDBOARD MOCKUP - SIX SPACER TUBES","Cut six equal strips, roll each to an 8 mm tube, and tape the 5 mm overlap flap.")
    c.setFillColor(INK); c.setFont("Helvetica-Bold",10); c.drawString(20*mm,PH-37*mm,"55 mm stand-offs between the two decks")
    # Six spacer-tube strips. Approx circumference of 8 mm tube with overlap flap.
    for i in range(6):
        x0=20*mm+(i%3)*48*mm
        y0=105*mm-(i//3)*67*mm
        c.setStrokeColor(RED); c.rect(x0,y0,30*mm,55*mm,stroke=1,fill=0)
        c.setStrokeColor(BLUE); c.setDash(2,1.5); c.line(x0+25*mm,y0,x0+25*mm,y0+55*mm); c.setDash()
        c.saveState(); c.translate(x0,y0); c.rotate(90); c.setFillColor(GRAY); c.setFont("Helvetica",6.5); c.drawCentredString(27.5*mm,-3*mm,"roll into 8 mm tube x 55"); c.restoreState()
    c.setFillColor(GRAY); c.setFont("Helvetica",7)
    c.drawString(20*mm,31*mm,"Each strip is 30 x 55 mm: about 25 mm circumference + 5 mm overlap flap.")
    c.drawString(20*mm,25*mm,"Make six. Tape each seam; trim the ends square so both plates sit level.")
    calibration_box(c, 230*mm, 20*mm)
    footer(c,11,"Do not use cardboard spacer tubes to support powered electronics or a moving robot.")
    c.showPage()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=PAGE, pageCompression=1)
    c.setTitle("VENTUNO Q sensor chassis - A4 cardboard mockup")
    c.setAuthor("PandoraBOX Body Runtime")
    overview_page(c)
    page = 2
    for deck in ("lower", "upper"):
        for section in ("front", "center", "rear"):
            piece_page(c, deck, section, page)
            page += 1
    holder_pages(c)
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
