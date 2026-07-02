"""
THEODORE'S WORLD — AI Image Generator
======================================
Generates all 136 character + scene images for the Theodore's World brand.
Claude writes each Higgsfield prompt. Theo + Super Theo are anchored to
the real Theodore photo for face accuracy.

Run: python generate_theo_images.py
Automatically resumes — skips already-generated files.
"""

import os
import sys
import time
import base64
import io
from pathlib import Path
from datetime import datetime
import anthropic
import httpx

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

CLAUDE_API_KEY    = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
HIGGSFIELD_API_KEY = os.getenv("HIGGSFIELD_API_KEY", "")

if not CLAUDE_API_KEY or not HIGGSFIELD_API_KEY:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "happy-hour-margarita" / "instagram-auto-post"))
        from config import CLAUDE_API_KEY as _ck, HIGGSFIELD_API_KEY as _hk
        CLAUDE_API_KEY = CLAUDE_API_KEY or _ck
        HIGGSFIELD_API_KEY = HIGGSFIELD_API_KEY or _hk
    except ImportError:
        raise RuntimeError("Missing API keys. Set ANTHROPIC_API_KEY and HIGGSFIELD_API_KEY in a .env file.")

os.environ['HF_KEY'] = HIGGSFIELD_API_KEY
import higgsfield_client

OUTPUT_FOLDER = Path(r"C:\Users\mamar\OneDrive\Desktop\TheoWorldImages")
LOG_FILE      = Path(__file__).parent / "log_theo_images.txt"
THEO_PHOTO    = Path(r"C:\Users\mamar\OneDrive\Desktop\New folder\0_1_640_N.webp")

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── STYLE & CHARACTER RULES ────────────────────────────────────────────────────

STYLE = (
    "3D Pixar Disney animation quality, smooth rounded 3D forms, soft warm lighting, "
    "vibrant child-friendly color palette, emotionally expressive faces, professional "
    "children's book illustration, ultra-high detail, cinematic quality rendering"
)

THEO_RULES = """
STRICT THEO CHARACTER RULES — EVERY RULE APPLIES TO EVERY SINGLE IMAGE, NO EXCEPTIONS:

BUILD: 8 years old, SLIM and LEAN — slender active child build, NOT chubby, NOT plump, NOT stocky.
Thin but healthy. Like a kid who runs around all day. Never wide or heavy-set.

FACE (use ONLY the provided reference photo — ignore any other version):
- Round face shape with FULL CHUBBY CHEEKS and SMALL BUTTON NOSE
- Big dark forest green eyes
- Dark brown thick curly hair — never straight or wavy
- Warm brown skin

CLOTHING — IDENTICAL IN EVERY IMAGE, NEVER CHANGES:
- Shirt: soft LAVENDER (light purple), hand-drawn fabric-marker PUZZLE PIECE on chest
- Pants: DARK NAVY JOGGERS, no visible tags
- LEFT shoe: RED SNEAKER
- RIGHT shoe: BLUE SNEAKER (mismatched on purpose — always)
- Headphones: NAVY noise-canceling, worn around NECK (never on ears)
- Backpack: WORN GRAY with butterfly pin on top zipper, gold star pin, rainbow patch,
  silver infinity ∞ button centered on front

CHARACTER CONSISTENCY: Every image of Theo must look like the SAME character.
Same face, same slim build, same outfit details. Do not vary ANY element.
"""

SUPER_THEO_RULES = """
STRICT SUPER THEO CHARACTER RULES — EVERY RULE APPLIES TO EVERY SINGLE IMAGE, NO EXCEPTIONS:

BUILD: 8 years old, SLIM and LEAN — slender active child build, NOT chubby, NOT plump, NOT stocky.
Thin but healthy. Shoulders back, chin up, fully confident posture. Never wide or heavy-set.

FACE (use ONLY the provided reference photo — ignore any other version):
- Round face shape with FULL CHUBBY CHEEKS and SMALL BUTTON NOSE
- LUMINOUS SILVER-GRAY eyes, lit from within
- Dark brown thick curly hair
- Warm brown skin

COSTUME — IDENTICAL IN EVERY IMAGE, NEVER CHANGES:
- Suit: LAVENDER-TO-PINK GRADIENT (soft pink at shoulders deepening to rich lavender at legs),
  shimmers faintly like butterfly wing fabric
- Cape: DARK NAVY, reaches past calves; inside lining = tiny GOLD STARS + thin constellation lines;
  clasped at collarbone with TWO SMALL GOLD CIRCULAR PINS
- Chest: BOLD GOLD INFINITY ∞ SYMBOL — slightly raised, metallic, glowing warmly
- LEFT boot: CHERRY RED, rounded toe, small gold star on outer ankle
- RIGHT boot: BRIGHT ROYAL BLUE (mismatched on purpose — always)
- Wrists: TWO SLIM GOLD CUFFS pulsing faint golden light

CHARACTER CONSISTENCY: Every image of Super Theo must look like the SAME character.
Same face, same slim build, same costume details. Do not vary ANY element.
"""

FLUTTER_RULES = """
Flutter character rules:
- Size: roughly size of a small bird
- Body: velvety deep purple
- Eyes: BRIGHT TURQUOISE, enormous, ancient and wise — NOT cartoonish
- Antennae: small with GOLD GLOWING ORB tips
- Wings: soft gold = calm/joyful | deep amber = alert/warning | blazing full gold = maximum power
"""

# ── ALL 136 DELIVERABLES ───────────────────────────────────────────────────────

DELIVERABLES = [
    # ── THEO CIVILIAN ──────────────────────────────────────────────────────────
    {"filename":"TheoC_01_Front.png","character":"theo_civilian",
     "description":"Civilian Theo, front view, full body, neutral friendly expression, standing naturally, white background"},
    {"filename":"TheoC_02_3Quarter.png","character":"theo_civilian",
     "description":"Civilian Theo, 3/4 view, full body, slight smile, white background"},
    {"filename":"TheoC_03_Side.png","character":"theo_civilian",
     "description":"Civilian Theo, side profile view, full body, looking forward, white background"},
    {"filename":"TheoC_04_Back.png","character":"theo_civilian",
     "description":"Civilian Theo, back view full body — backpack clearly shown: butterfly pin top zipper, gold star pin, rainbow patch, silver ∞ button centered — each detail rendered clearly, white background"},
    {"filename":"TheoC_05_Expr_Curious.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression CURIOUS — eyebrows raised, eyes wide and searching, head tilted slightly LEFT, mouth slightly open like he noticed something fascinating"},
    {"filename":"TheoC_06_Expr_Happy.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression HAPPY — full warm smile, eyes crinkled with genuine joy, cheeks raised"},
    {"filename":"TheoC_07_Expr_Overwhelmed.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression OVERWHELMED — eyes slightly too wide, hands near ears, brow furrowed, a child trying very hard to hold on"},
    {"filename":"TheoC_08_Expr_Calm.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression CALM — eyes soft and settled, neutral gentle mouth, peaceful and grounded"},
    {"filename":"TheoC_09_Expr_Determined.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression DETERMINED — jaw set, eyes focused and certain, quiet inner strength visible"},
    {"filename":"TheoC_10_Expr_Thinking.png","character":"theo_civilian",
     "description":"Civilian Theo face portrait, expression THINKING — head tilted distinctly to the LEFT, eyes slightly unfocused and upward, processing, gentle and internal"},
    {"filename":"TheoC_11_BackpackDetail.png","character":"prop",
     "description":"Close-up detail of worn gray child's backpack: butterfly pin on top zipper, gold star pin, rainbow patch, silver infinity ∞ button centered on front — each element clear and beautiful, white background, slightly magical feel"},
    {"filename":"TheoC_12_Walking.png","character":"theo_civilian",
     "description":"Civilian Theo walking to school on NYC sidewalk, morning light, backpack on, headphones around neck, mid-stride, NYC brownstone buildings, elevated train line visible, real grounded neighborhood"},
    {"filename":"TheoC_13_Desk.png","character":"theo_civilian",
     "description":"Civilian Theo sitting at school desk, spiral notebook open, pen in hand, head tilted left thinking, warm afternoon classroom light"},
    {"filename":"TheoC_14_Breakfast.png","character":"theo_civilian",
     "description":"Civilian Theo eating breakfast at home, plate of golden waffles, counting bites quietly, warm morning kitchen light, cozy safe home"},
    {"filename":"TheoC_15_InfinityPress.png","character":"theo_civilian",
     "description":"Civilian Theo sitting quietly, thumb gently pressed to the silver ∞ button on his backpack — close private moment, soft warm light, expression: calm and grounded"},
    {"filename":"TheoC_16_Fence.png","character":"theo_civilian",
     "description":"Civilian Theo standing at a chain-link fence looking through it, observing and processing — slightly apart, thoughtful and peaceful, urban setting, soft light"},
    {"filename":"TheoC_17_FrontSteps.png","character":"theo_civilian",
     "description":"Civilian Theo sitting on NYC brownstone front steps with Dad beside him — tender quiet moment, both looking forward, warm late afternoon light, sense of safety and love"},

    # ── SUPER THEO ─────────────────────────────────────────────────────────────
    {"filename":"SuperTheo_01_Front.png","character":"super_theo",
     "description":"Super Theo, front view, full body, standing tall, confident posture, white background"},
    {"filename":"SuperTheo_02_3Quarter.png","character":"super_theo",
     "description":"Super Theo, 3/4 view, full body, chin up, slight smile, white background"},
    {"filename":"SuperTheo_03_Side.png","character":"super_theo",
     "description":"Super Theo, side profile view, full body, cape flowing gently, white background"},
    {"filename":"SuperTheo_04_Back.png","character":"super_theo",
     "description":"Super Theo, back view full body — dark navy cape exterior visible, inside lining showing tiny gold stars and constellation lines, two gold clasp pins at collarbone, white background"},
    {"filename":"SuperTheo_05_Expr_Determined.png","character":"super_theo",
     "description":"Super Theo face portrait, expression DETERMINED — jaw set, silver-gray eyes locked on target, unshakeable resolve"},
    {"filename":"SuperTheo_06_Expr_CalmCertainty.png","character":"super_theo",
     "description":"Super Theo face portrait, expression CALM CERTAINTY — silver-gray eyes steady, mouth relaxed, the peace of someone who knows exactly what they are doing"},
    {"filename":"SuperTheo_07_Expr_PureJoy.png","character":"super_theo",
     "description":"Super Theo face portrait, expression PURE JOY — full bright smile, silver-gray eyes lit and sparkling, absolute happiness"},
    {"filename":"SuperTheo_08_Expr_Alert.png","character":"super_theo",
     "description":"Super Theo face portrait, expression ALERT — eyes sharpened and scanning, silver-gray focused, sensing something before it happens"},
    {"filename":"SuperTheo_09_Expr_Brave.png","character":"super_theo",
     "description":"Super Theo face portrait, expression BRAVE — chin up, silver-gray eyes forward, quiet fierce courage, not fearless but doing it anyway"},
    {"filename":"SuperTheo_10_Expr_Whispering.png","character":"super_theo",
     "description":"Super Theo face portrait — eyes gently closed, lips moving in a quiet whisper 'I am enough', peaceful and certain, deeply private powerful moment, soft warm golden light"},
    {"filename":"SuperTheo_11_Detail_Chest.png","character":"prop",
     "description":"Extreme close-up of Super Theo's chest — bold gold infinity ∞ symbol, slightly raised metallic glowing warmly, on lavender-to-pink gradient suit fabric that shimmers like butterfly wings, white background"},
    {"filename":"SuperTheo_12_Detail_Cape.png","character":"prop",
     "description":"Close-up of Super Theo's cape INSIDE LINING — dark navy fabric, tiny gold stars everywhere, thin constellation lines connecting them, two small gold circular clasp pins at top edge, white background"},
    {"filename":"SuperTheo_13_Detail_Cuff.png","character":"prop",
     "description":"Close-up of Super Theo's slim gold wrist cuff — cool solid metal, pulsing faint golden light visible, white background"},
    {"filename":"SuperTheo_14_Detail_Boot.png","character":"prop",
     "description":"Close-up of Super Theo's LEFT boot — cherry red, rounded toe, small gold star embossed on outer ankle, white background"},
    {"filename":"SuperTheo_15_HeroPose.png","character":"super_theo",
     "description":"MASTER BRAND IMAGE — Super Theo SIGNATURE HERO POSE: standing perfectly tall, arms at sides, chin up, silver-gray eyes forward, cape flowing gently, pure white background — this is the definitive hero image"},
    {"filename":"SuperTheo_16_Flying.png","character":"super_theo",
     "description":"Super Theo flying through NYC night sky — arms forward or cape spread wide, golden light trail behind him, NYC skyline below with lit windows and bridges, stars above, triumphant and free"},
    {"filename":"SuperTheo_17_Transform.png","character":"super_theo",
     "description":"Super Theo mid-transformation — hand pressed to glowing ∞ button, eyes closed, explosive gold light bursting outward from chest in all directions, lavender glow surrounding him, Flutter blazing gold nearby"},
    {"filename":"SuperTheo_18_HyperfocusBeam.png","character":"super_theo",
     "description":"Super Theo HYPERFOCUS BEAM — silver-gray eyes intensely sharp, visible beam of crystalline light projecting from his gaze, seeing what no one else can, determined expression"},
    {"filename":"SuperTheo_19_EmpathyShield.png","character":"super_theo",
     "description":"Super Theo EMPATHY SHIELD — hand flat on chest over gold ∞, warm golden glow radiating outward from heart like a heartbeat pulse, protective and loving energy"},
    {"filename":"SuperTheo_20_DetailVision.png","character":"super_theo",
     "description":"Super Theo DETAIL VISION — scanning into the distance, silver-gray eyes laser sharp, subtle grid or signal lines visible in the air, noticing what everyone else missed"},
    {"filename":"SuperTheo_21_AtMachine.png","character":"super_theo",
     "description":"Super Theo at Dr. Norm's gray machine — both hands on the dials, focused and determined, gray cold machine in front of him, his warm lavender suit and gold glow contrasting the cold gray room"},
    {"filename":"SuperTheo_22_GoldSparks.png","character":"super_theo",
     "description":"Super Theo — hands stretched out calm but powerful, fine gold sparks and light flowing from fingertips, not aggressive, pure controlled energy, white or dark dramatic background"},
    {"filename":"SuperTheo_23_Victory.png","character":"super_theo",
     "description":"Super Theo VICTORY — arms raised high, gold sparks and stars exploding outward all around him, pure joy on his face, triumphant, silver-gray eyes lit and happy"},
    {"filename":"SuperTheo_24_Calm.png","character":"super_theo",
     "description":"Super Theo CALM BREATHING — sitting cross-legged on ground, eyes gently closed, peaceful expression, soft warm golden light around him, completely at rest, centered"},

    # ── FLUTTER ────────────────────────────────────────────────────────────────
    {"filename":"Flutter_01_Front_Gold.png","character":"flutter",
     "description":"Flutter the butterfly, front view, wings fully spread, SOFT GOLD wings (calm joyful), deep purple velvety body, enormous bright turquoise ancient-wisdom eyes, gold glowing orb antennae tips, white background"},
    {"filename":"Flutter_02_3Quarter.png","character":"flutter",
     "description":"Flutter, 3/4 view, perched with wings slightly open, deep purple body, bright turquoise ancient eyes, gold antennae tips glowing, white background"},
    {"filename":"Flutter_03_WingRef_Gold.png","character":"flutter",
     "description":"Flutter wing color reference — SOFT GOLD wings fully spread, meaning: Calm / Safe / Joyful. Deep purple body, turquoise eyes, white background"},
    {"filename":"Flutter_04_WingRef_Amber.png","character":"flutter",
     "description":"Flutter wing color reference — DEEP AMBER wings fully spread, meaning: Alert / Warning. Deep purple body, turquoise eyes sharper, antennae pointed forward, white background"},
    {"filename":"Flutter_05_WingRef_Blazing.png","character":"flutter",
     "description":"Flutter wing color reference — BLAZING FULL GOLD wings at maximum power, wings radiating golden light, deep purple body glowing, turquoise eyes intense and ancient, white background"},
    {"filename":"Flutter_06_ScaleRef.png","character":"flutter",
     "description":"Scale reference — Flutter perched on Super Theo's shoulder: roughly the size of a small bird, clearly visible, soft gold wings, deep purple body, both looking forward, white background"},
    {"filename":"Flutter_07_InMotion.png","character":"flutter",
     "description":"Flutter in motion, flying with wings open, fine gold dust trail streaming behind her, deep purple body, turquoise eyes, white or light background"},
    {"filename":"Flutter_08_SoloBlaze.png","character":"flutter",
     "description":"KEY BRAND IMAGE — Flutter SOLO BLAZING: wings at maximum blazing gold fully spread, deep purple body lit with golden energy, turquoise eyes blazing with ancient power, gold dust everywhere, pure white background"},
    {"filename":"Flutter_09_Alert.png","character":"flutter",
     "description":"Flutter ALERT pose — wings deep amber, antennae pointed sharply forward, turquoise eyes focused and intense, body tense and ready, white background"},
    {"filename":"Flutter_10_Perched.png","character":"flutter",
     "description":"Flutter perched on civilian Theo's shoulder — calm soft gold wings, looking forward alongside him, ancient wisdom in her turquoise eyes, peaceful companion"},
    {"filename":"Flutter_11_Diving.png","character":"flutter",
     "description":"Flutter DIVING — wings folded tight against body, deep amber color, mid-action descending fast, turquoise eyes locked on target, gold dust trail"},
    {"filename":"Flutter_12_Resting.png","character":"flutter",
     "description":"Flutter resting on Theo's knee — civilian Theo sitting, Flutter wings folded gently, calm soft gold, peaceful and gentle, a quiet companion moment"},

    # ── MOM ────────────────────────────────────────────────────────────────────
    {"filename":"Mom_01_Front.png","character":"mom",
     "description":"Mom character, front view, full body — warm real relatable woman, not idealized, a parent who has been through hard days and shows it with grace not exhaustion, warm kind eyes, comfortable everyday clothes, 3D Pixar style, white background"},
    {"filename":"Mom_02_3Quarter.png","character":"mom",
     "description":"Mom, 3/4 view, full body, warm expression, 3D Pixar style, white background"},
    {"filename":"Mom_03_Expr_Loving.png","character":"mom",
     "description":"Mom face portrait, expression WARM AND LOVING — eyes soft and full of love, gentle smile that comes from knowing her child completely"},
    {"filename":"Mom_04_Expr_Concerned.png","character":"mom",
     "description":"Mom face portrait, expression CONCERNED — brow slightly furrowed, eyes watchful, paying close attention, not panicked but alert"},
    {"filename":"Mom_05_Expr_Proud.png","character":"mom",
     "description":"Mom face portrait, expression PROUD — eyes bright with pride, smile full and warm, watching something wonderful"},
    {"filename":"Mom_06_Expr_Laughing.png","character":"mom",
     "description":"Mom face portrait, expression LAUGHING — genuine open laugh, eyes crinkled, completely joyful"},
    {"filename":"Mom_07_Expr_Tender.png","character":"mom",
     "description":"Mom face portrait, expression TENDER — eyes soft and full of gentle love, slight smile, the face of someone who would do anything"},
    {"filename":"Mom_08_HandOnShoulder.png","character":"mom",
     "description":"Mom with hand gently on civilian Theo's shoulder — 'I'm right here' moment, Theo looks up at her, warm home light, tender connection between them"},
    {"filename":"Mom_09_Breakfast.png","character":"mom",
     "description":"Mom making breakfast in warm home kitchen, morning light streaming in, golden waffles visible, Theo at table in background, safe warm domestic love"},
    {"filename":"Mom_10_WatchingPride.png","character":"mom",
     "description":"Mom watching Theo from a distance with quiet pride — not interrupting, just watching, eyes full, proud of who her child is"},

    # ── DAD ────────────────────────────────────────────────────────────────────
    {"filename":"Dad_01_Front.png","character":"dad",
     "description":"Dad character, front view, full body — warm strong gentle man, real and grounded, kind eyes, natural presence, present in the ways that count, 3D Pixar style, white background"},
    {"filename":"Dad_02_3Quarter.png","character":"dad",
     "description":"Dad, 3/4 view, full body, warm grounded expression, 3D Pixar style, white background"},
    {"filename":"Dad_03_Expr_Loving.png","character":"dad",
     "description":"Dad face portrait, expression WARM AND LOVING — eyes full and present, the love of a father who means everything"},
    {"filename":"Dad_04_Expr_Proud.png","character":"dad",
     "description":"Dad face portrait, expression PROUD — eyes bright, jaw slightly tight with emotion watching his son"},
    {"filename":"Dad_05_Expr_Tender.png","character":"dad",
     "description":"Dad face portrait, expression TENDER — soft eyes, gentle mouth, the quietest most complete kind of love"},
    {"filename":"Dad_06_Expr_Thoughtful.png","character":"dad",
     "description":"Dad face portrait, expression THOUGHTFUL — eyes somewhere else briefly, thinking about something important, gentle"},
    {"filename":"Dad_07_FrontSteps.png","character":"dad",
     "description":"CRITICAL EMOTIONAL IMAGE — Dad and young Theo on NYC brownstone front steps: Dad pressing the small silver infinity ∞ button into Theo's small palm, BOTH HANDS covering Theo's hand, Theo looking down at the button, Dad looking at Theo with everything he has — warm late afternoon golden light, this moment explains why that button is everything"},
    {"filename":"Dad_08_HandOnShoulder.png","character":"dad",
     "description":"Dad standing with his hand on civilian Theo's shoulder — quiet strength passing between them, warm light, grounded love"},
    {"filename":"Dad_09_QuietPride.png","character":"dad",
     "description":"Dad looking at Theo from nearby with quiet pride — not interrupting, just watching, eyes full, proud of who his boy is"},

    # ── MS. OKAFOR ─────────────────────────────────────────────────────────────
    {"filename":"MsOkafor_01_Front.png","character":"ms_okafor",
     "description":"Ms. Okafor, front view, full body — perceptive and genuinely warm teacher who sees every student, professional but approachable, warm bright eyes, natural presence, 3D Pixar style, white background"},
    {"filename":"MsOkafor_02_Expr_Welcoming.png","character":"ms_okafor",
     "description":"Ms. Okafor face portrait, expression WELCOMING — open warm smile, eyes that say 'you belong here', arms slightly open"},
    {"filename":"MsOkafor_03_Expr_Proud.png","character":"ms_okafor",
     "description":"Ms. Okafor face portrait, expression PROUD — eyes shining, smile that says 'I always knew you could'"},
    {"filename":"MsOkafor_04_Expr_Thoughtful.png","character":"ms_okafor",
     "description":"Ms. Okafor face portrait, expression THOUGHTFUL — eyes soft and considering, really seeing a student, the look of a teacher who pays attention"},
    {"filename":"MsOkafor_05_Expr_Delighted.png","character":"ms_okafor",
     "description":"Ms. Okafor face portrait, expression DELIGHTED — genuine surprise and joy, something wonderful just happened"},
    {"filename":"MsOkafor_06_Classroom.png","character":"ms_okafor",
     "description":"Ms. Okafor standing at the front of Room 14 classroom, warm and open, arm slightly extended welcoming students, 'Our Different Brilliances' wall of student cards visible behind her, warm afternoon light"},
    {"filename":"MsOkafor_07_Wall.png","character":"ms_okafor",
     "description":"Ms. Okafor at the 'Our Different Brilliances' wall — hundreds of student-written cards pinned everywhere — hand pressed gently to her chest, eyes full of emotion, this wall is her life's work"},

    # ── MARCUS ─────────────────────────────────────────────────────────────────
    {"filename":"Marcus_01_Front.png","character":"marcus",
     "description":"Marcus, 8-year-old boy, front view full body — warm medium-brown skin, short neat locs, dark brown focused eyes behind ROUND WIRE-FRAMED GLASSES, slim lean build, clothes with visible pockets, pencils sorted by length on desk beside him, 3D Pixar style, white background"},
    {"filename":"Marcus_02_3Quarter.png","character":"marcus",
     "description":"Marcus, 3/4 view full body, focused precise expression, round glasses, neat locs, sorted pencils visible, white background"},
    {"filename":"Marcus_03_Expr_Focused.png","character":"marcus",
     "description":"Marcus face portrait, expression FOCUSED AND SORTING — eyes precise and concentrated, pencils sorted by length, quietly brilliant, this is where he is most himself"},
    {"filename":"Marcus_04_Expr_Confused.png","character":"marcus",
     "description":"Marcus face portrait, expression CONFUSED AND DISTRESSED — pencils in a disorganized pile, something is deeply wrong, brow furrowed, eyes unsettled — his order is broken"},
    {"filename":"Marcus_05_Expr_Relieved.png","character":"marcus",
     "description":"Marcus face portrait, expression RELIEVED AND RESTORED — pencils sorted again by length, small quiet smile, order returned, breathing again"},

    # ── PRIYA ──────────────────────────────────────────────────────────────────
    {"filename":"Priya_01_Front.png","character":"priya",
     "description":"Priya, 8-year-old girl, front view full body — light brown skin, long dark hair in a LOOSE BRAID slightly coming undone, dark brown soft observant eyes, slight small build, comfortable layered clothing, PENCIL SMUDGE on her hand, notebook with tiny bird drawings in every margin, 3D Pixar style, white background"},
    {"filename":"Priya_02_3Quarter.png","character":"priya",
     "description":"Priya, 3/4 view full body, gentle expression, loose braid, pencil smudge on hand, notebook with bird drawings, white background"},
    {"filename":"Priya_03_Expr_Drawing.png","character":"priya",
     "description":"Priya face portrait, expression ABSORBED IN DRAWING — eyes down and completely focused, mouth slightly open in concentration, pencil in hand, this is where she lives"},
    {"filename":"Priya_04_Expr_Blank.png","character":"priya",
     "description":"Priya face portrait, expression BLANK AND WRONG — notebook closed, hands completely still, eyes unfocused — the absence of her art is the absence of her"},
    {"filename":"Priya_05_Expr_Bright.png","character":"priya",
     "description":"Priya face portrait, expression BRIGHT AND DRAWING AGAIN — eyes alive, small bright smile, tiny flock of birds appearing to fly off the edge of her notebook page"},

    # ── JAMES ──────────────────────────────────────────────────────────────────
    {"filename":"James_01_Front.png","character":"james",
     "description":"James, 8-year-old boy, front view full body — dark brown skin, short tight curls, dark brown wide expressive eyes, TALL for his age with long legs, wearing sports team jersey or hoodie in team colors, knee slightly bent like it wants to bounce, 3D Pixar style, white background"},
    {"filename":"James_02_3Quarter.png","character":"james",
     "description":"James, 3/4 view full body, energetic expression, sports jersey, wide expressive eyes, tall build, white background"},
    {"filename":"James_03_Expr_Excited.png","character":"james",
     "description":"James face portrait, expression EXCITED AND FULLY HIMSELF — big bright grin, eyes wide and alive, energy visible in his whole face, leaning slightly forward"},
    {"filename":"James_04_Expr_Flat.png","character":"james",
     "description":"James face portrait, expression FLAT AND STILL — all that energy gone, eyes dim, the stillness looks completely wrong on him — something is terribly wrong"},
    {"filename":"James_05_Expr_LitUp.png","character":"james",
     "description":"James face portrait, expression LIT UP AGAIN — leaning forward, animated, fully back, eyes wide and passionate, the energy returned completely"},

    # ── DESTINY ────────────────────────────────────────────────────────────────
    {"filename":"Destiny_01_Front.png","character":"destiny",
     "description":"Destiny, 8-year-old girl, front view full body — warm brown skin, BRIGHT RED BRAIDS (her signature, always styled), dark brown sharp perceptive eyes that notice everything, medium grounded build, comfortable but put-together outfit, 3D Pixar style, white background"},
    {"filename":"Destiny_02_3Quarter.png","character":"destiny",
     "description":"Destiny, 3/4 view full body, perceptive expression, bright red braids, sharp eyes, white background"},
    {"filename":"Destiny_03_Expr_Thinking.png","character":"destiny",
     "description":"Destiny face portrait, expression THINKING AND ROCKING — faraway focused look, barely perceptible rocking motion, processing something deep, perceptive and present"},
    {"filename":"Destiny_04_Expr_Still.png","character":"destiny",
     "description":"Destiny face portrait, expression PERFECTLY STILL AND BLANK — no rocking, no nod, eyes unfocused — the complete stillness looks wrong and unsettling on her"},
    {"filename":"Destiny_05_Expr_Restored.png","character":"destiny",
     "description":"Destiny face portrait, expression ROCKING AGAIN — small knowing nod, she's back, quiet confidence restored, perceptive eyes alive again"},

    # ── CLASSMATES GROUP SHOT ──────────────────────────────────────────────────
    {"filename":"Classmates_GroupShot.png","character":"group",
     "description":"Classroom group shot — all 4 classmates at desks being fully themselves: MARCUS sorting pencils by length with small smile (round glasses neat locs), PRIYA drawing birds in notebook margins (loose braid pencil smudge on hand), JAMES leaning forward animated in sports jersey (tall, knee bouncing), DESTINY with bright red braids giving knowing nod — MS. OKAFOR warmly visible at front, 'Our Different Brilliances' wall behind her, warm afternoon golden light, every child distinct and alive"},

    # ── DR. NORM ───────────────────────────────────────────────────────────────
    {"filename":"DrNorm_01_Front.png","character":"dr_norm",
     "description":"Dr. Norm, front view full body — VERY TALL and rigid like a ruler dressed in a suit, VERY PALE skin, hair slicked PERFECTLY FLAT not one strand loose, FLAT GRAY eyes, white lab coat over pressed charcoal suit, thin silver glasses precisely placed, clipboard with single pen at exact angle, thin flat measured smile that does NOT reach his eyes, 3D Pixar style, white background"},
    {"filename":"DrNorm_02_3Quarter.png","character":"dr_norm",
     "description":"Dr. Norm, 3/4 view full body, perfectly rigid posture, clipboard, pale skin, flat gray eyes, white lab coat, white background"},
    {"filename":"DrNorm_03_Expr_Smile.png","character":"dr_norm",
     "description":"Dr. Norm face portrait, expression MEASURED SMILE — thin flat smile drawn as if with a template, does not reach his flat gray eyes at all, deeply unsettling precision"},
    {"filename":"DrNorm_04_Expr_Cold.png","character":"dr_norm",
     "description":"Dr. Norm face portrait, expression COLD CALCULATING — flat gray eyes studying something, pen poised, making a clinical assessment, absolutely no warmth"},
    {"filename":"DrNorm_05_Expr_Defeated.png","character":"dr_norm",
     "description":"Dr. Norm face portrait, expression FALTERING AND SMALL — the rigid certainty cracking, looking smaller than he is, exposed, precision starting to fail"},
    {"filename":"DrNorm_06_Machine.png","character":"prop",
     "description":"Dr. Norm's machine STANDALONE — gray metal filing-cabinet-sized box, few dials on front, small screen, single antenna on top, cold gray waves radiating outward, looks almost ordinary — that's what makes it unsettling, white background"},
    {"filename":"DrNorm_07_EnteringRoom14.png","character":"dr_norm",
     "description":"Dr. Norm entering Room 14 doorway — framed in the doorway, very tall and precise, class visible looking up at him, clipboard raised, thin smile, cold presence entering a warm classroom"},
    {"filename":"DrNorm_08_WatchingLunch.png","character":"dr_norm",
     "description":"Dr. Norm watching Theo at lunch — Theo at cafeteria table by window, Dr. Norm standing nearby with clipboard raised and flat smile, making a clinical mark, cold observation"},
    {"filename":"DrNorm_09_AtMachine.png","character":"dr_norm",
     "description":"Dr. Norm in his cold gray office beside his machine — perfectly aligned desk, no photos or plants, cold gray light, standing with certainty next to the machine, hand on dial"},
    {"filename":"DrNorm_10_Confrontation.png","character":"dr_norm",
     "description":"Dr. Norm in confrontation with Super Theo — across the cracking broken machine from Super Theo, gold light pouring through gray cracks, Dr. Norm looking smaller now, rigid certainty crumbling"},

    # ── SENSORY SIREN ──────────────────────────────────────────────────────────
    {"filename":"SensorySiren_01_Front.png","character":"sensory_siren",
     "description":"Sensory Siren villain, front view full body — loud chaotic visually overstimulating design, harsh clashing colors throughout, sharp jagged design elements everywhere, speaker and sound devices integrated as weapons, the entire design feels like TOO MUCH AT ONCE, overwhelming visual noise made into a character, 3D Pixar style, white background"},
    {"filename":"SensorySiren_02_Expr_Attack.png","character":"sensory_siren",
     "description":"Sensory Siren face portrait, expression AGGRESSIVE ATTACK — mouth open releasing visible sound waves, harsh clashing colors, overwhelming chaotic energy"},
    {"filename":"SensorySiren_03_Expr_Laugh.png","character":"sensory_siren",
     "description":"Sensory Siren face portrait, expression MOCKING LAUGH — cruel amusement, sharp chaotic colors, overwhelming"},

    # ── MASK MASTER ────────────────────────────────────────────────────────────
    {"filename":"MaskMaster_01_Front.png","character":"mask_master",
     "description":"Mask Master villain, front view full body — theatrical and unsettling, wears MANY LAYERED MASKS, different faces visible in layers, costume feels layered and deceptive, charming on the surface sinister underneath, theatricality hiding something darker, 3D Pixar style, white background"},
    {"filename":"MaskMaster_02_Expr_Charming.png","character":"mask_master",
     "description":"Mask Master face portrait, expression CHARMING FALSE SMILE — front mask pleasant and appealing but eyes don't match the smile, something wrong underneath"},
    {"filename":"MaskMaster_03_Expr_Sinister.png","character":"mask_master",
     "description":"Mask Master face portrait, expression SINISTER BENEATH MASK — the mask slipping slightly, true face showing underneath, unsettling and deceptive"},

    # ── THE ISOLATOR ───────────────────────────────────────────────────────────
    {"filename":"Isolator_01_Front.png","character":"isolator",
     "description":"The Isolator villain, front view full body — cold distant calculated, costume incorporates wall and barrier motifs (walls dividers barriers built into the outfit design), builds invisible distance, design feels withdrawn and separating, 3D Pixar style, white background"},
    {"filename":"Isolator_02_Expr_Cold.png","character":"isolator",
     "description":"The Isolator face portrait, expression COLD AND DISTANT — empty eyes, everything pushed away, impossible to reach"},
    {"filename":"Isolator_03_Expr_Calculated.png","character":"isolator",
     "description":"The Isolator face portrait, expression CALCULATED WATCH — eyes studying and measuring the distance between people, calculating how to make it wider"},

    # ── SCHOOL — RIDGECREST ELEMENTARY ─────────────────────────────────────────
    {"filename":"School_01_Exterior.png","character":"location",
     "description":"Ridgecrest Elementary exterior — two-story brick building, big windows, urban NYC neighborhood, large colorful mural across front wall showing children of all sizes running laughing reading playing music, center of mural: bold blue and yellow letters 'EVERY CHILD BELONGS HERE', elevated train line nearby, corner bakery in sight, sidewalk approach, warm morning light"},
    {"filename":"School_02_Room14.png","character":"location",
     "description":"Room 14 classroom interior — warm lived-in safe, desks in rows with enough space, 'Our Different Brilliances' wall covered in student-written cards in different handwriting, large windows with afternoon light moving across floor, no assigned seats feeling, welcoming and real"},
    {"filename":"School_03_DrNormOffice.png","character":"location",
     "description":"Dr. Norm's office interior — small gray room at end of hall, everything perfectly aligned, no photos no plants no coffee mug no mess, the machine (gray metal filing-cabinet-sized, dials, small screen, single antenna) in the corner, cold gray light, all warmth drained from this room"},
    {"filename":"School_04_Hallway_Day.png","character":"location",
     "description":"Ridgecrest Elementary hallway DAY — busy and alive, scuff marks on floor from a thousand shoes, fingerprints on water fountain, bulletin boards with student collages in different handwriting and sizes, warm school day energy"},
    {"filename":"School_05_Hallway_Night.png","character":"location",
     "description":"Ridgecrest Elementary hallway NIGHT — same hallway but empty and still, lit only by exit signs and dim overhead light, scuff marks visible, bulletin boards ghostly in low light, the school breathing quietly alone"},

    # ── KEY SCENES ─────────────────────────────────────────────────────────────
    {"filename":"Scene_01_HeroPose.png","character":"super_theo",
     "description":"MASTER BRAND IMAGE — Super Theo and Flutter SIGNATURE HERO POSE: Super Theo standing tall perfectly confident on pure white background, Flutter beside him with blazing full gold wings spread wide, gold light all around both of them, the definitive Theodore's World hero image"},
    {"filename":"Scene_02_CivilianCompanion.png","character":"theo_civilian",
     "description":"Civilian Theo and Flutter everyday companion — Theo walking or standing naturally, Flutter perched on his shoulder with calm soft gold wings, both looking forward together, warm gentle light, real and quiet"},
    {"filename":"Scene_03_Transformation.png","character":"super_theo",
     "description":"TRANSFORMATION SCENE — Theo mid-transformation: hand pressed to glowing ∞ button, eyes closed, gold light bursting outward from chest in all directions, civilian clothes dissolving into hero suit, Flutter blazing gold nearby filling the air with golden light"},
    {"filename":"Scene_04_Flying.png","character":"super_theo",
     "description":"Super Theo FLYING over NYC night sky — arms forward or cape spread wide, gold light trail streaming behind him, NYC skyline below with lit windows bridges and water, stars above city glow below, triumphant and free"},
    {"filename":"Scene_05_DadSteps.png","character":"dad",
     "description":"EMOTIONALLY CRITICAL SCENE — Dad and young Theo on NYC brownstone front steps: Dad pressing the small silver infinity button into Theo's small palm, both hands covering Theo's hand, Theo looking down at the button, Dad looking at Theo with everything — warm late afternoon golden light, this moment is why that button is everything"},
    {"filename":"Scene_06_MomKitchen.png","character":"mom",
     "description":"Mom and civilian Theo morning kitchen — warm home kitchen, morning light streaming through window, golden waffles on the table, Mom nearby in kitchen, Theo at table, safe warm domestic love"},
    {"filename":"Scene_07_DrNormReveal.png","character":"dr_norm",
     "description":"Villain intro — Dr. Norm in his cold gray office with his machine: standing beside the gray filing-cabinet machine, cold gray light, precise posture, thin smile, the machine humming with cold gray waves, unsettling normalcy"},
    {"filename":"Scene_08_Battle.png","character":"super_theo",
     "description":"BATTLE AT THE MACHINE — Super Theo with both hands on the machine dials focused and determined, Flutter diving amber wings sharp above, Dr. Norm visible in background looking uncertain, gold and gray light clashing, intense action"},
    {"filename":"Scene_09_MachineBreaking.png","character":"super_theo",
     "description":"CLIMAX SCENE — Machine breaking: the gray machine cracking apart, warm gold light flooding through every crack, gray being replaced by gold everywhere, Super Theo before it silver-gray eyes blazing, Flutter at maximum blazing gold spread wide — gold defeating gray"},
    {"filename":"Scene_10_ClassroomRestored.png","character":"group",
     "description":"RESOLUTION SCENE — Classroom morning all friends restored: Theo at his desk, Marcus sorting pencils with small smile, Priya drawing birds in notebook margin, James leaning forward animated and alive, Destiny rocking gently with knowing nod, Ms. Okafor at front beaming, 'Our Different Brilliances' wall glowing behind her, warm golden light, everyone exactly themselves"},
    {"filename":"Scene_11_AllVillains.png","character":"group",
     "description":"Series reference — all 4 villains group shot: Dr. Norm (tall rigid pale clipboard), Sensory Siren (chaotic clashing colors), Mask Master (theatrical layered masks), The Isolator (cold barrier motifs) — standing together, dark dramatic backdrop, each distinct and threatening"},
    {"filename":"Scene_12_DiverseFriends.png","character":"super_theo",
     "description":"Community image — Super Theo in hero pose surrounded by 4 diverse children of different backgrounds and appearances, warm group energy, gold light around all of them, community and belonging, bright and hopeful"},
]

# ── CLAUDE PROMPT BUILDER ──────────────────────────────────────────────────────

def get_rules(character: str) -> str:
    if character == "theo_civilian":
        return THEO_RULES
    elif character == "super_theo":
        return SUPER_THEO_RULES
    elif character == "flutter":
        return FLUTTER_RULES
    else:
        return ""

def build_higgsfield_prompt(item: dict, theo_face_desc: str, client: anthropic.Anthropic) -> str:
    character   = item["character"]
    description = item["description"]
    rules       = get_rules(character)
    uses_theo   = character in ("theo_civilian", "super_theo")

    # For Theo/SuperTheo — the FIXED face description is injected verbatim every time.
    # Claude only writes the scene/action part. This keeps the face identical across all images.
    if uses_theo:
        prompt_request = f"""You are the art director for Theodore's World, a 3D Pixar-quality children's book brand.

Write a Higgsfield AI image prompt for this scene. The CHARACTER DESCRIPTION below is FIXED and must be copied EXACTLY into your prompt — do not rephrase or summarize it.

FIXED CHARACTER DESCRIPTION (copy this verbatim into the prompt):
{theo_face_desc}

FIXED CHARACTER RULES (enforce exactly):
{rules}

SCENE TO ILLUSTRATE:
{description}

GLOBAL STYLE: {STYLE}

Instructions:
- Start the prompt with the fixed character description word for word
- Then add the scene details
- Then add the style
- Keep total under 220 words
- Output ONLY the prompt — no intro, no quotes

Write the prompt now:"""
    else:
        prompt_request = f"""You are the art director for Theodore's World, a 3D Pixar-quality children's book brand.

Write a single detailed Higgsfield AI image prompt.

IMAGE NEEDED: {description}

{rules}

GLOBAL STYLE: {STYLE}

- Be extremely specific about every visual element
- Include colors, lighting, mood, camera angle
- Keep it under 200 words
- Output ONLY the prompt — no intro, no explanation, no quotes

Write the prompt now:"""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt_request}]
    )
    return response.content[0].text.strip()


FACE_CACHE = Path(__file__).parent / "theo_face_description.txt"

def analyze_theo_face(client: anthropic.Anthropic) -> str:
    # Use cached description if it exists — guarantees identical text every run
    if FACE_CACHE.exists():
        desc = FACE_CACHE.read_text(encoding="utf-8").strip()
        log(f"Using cached face description: {desc[:100]}...")
        return desc

    log("Analyzing Theodore's character reference image...")
    from PIL import Image
    img = Image.open(THEO_PHOTO).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=350,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_data}},
                {"type": "text", "text": (
                    "This is the OFFICIAL character design reference for Theodore ('Theo') from Theodore's World. "
                    "Write a precise, detailed physical description of this character for a 3D Pixar animator to recreate EXACTLY. "
                    "Include: exact face shape, cheek fullness, nose shape and size, eye color and size, "
                    "eyebrow shape, hair color/texture/style, skin tone, chin shape, ear shape, "
                    "overall head proportions, and the specific feeling this face conveys. "
                    "Be so specific that any artist reading this produces the SAME face every time. "
                    "6-8 sentences. Only physical description — no story, no names, no extra context."
                )}
            ]
        }]
    )
    desc = response.content[0].text.strip()
    # Save to cache so every run uses identical wording
    FACE_CACHE.write_text(desc, encoding="utf-8")
    log(f"Face description saved to cache: {desc[:100]}...")
    return desc


def generate_image(prompt: str) -> str:
    result = higgsfield_client.subscribe(
        "bytedance/seedream/v4/text-to-image",
        {
            "prompt": prompt,
            "resolution": "2K",
            "aspect_ratio": "1:1",
            "camera_fixed": False
        }
    )
    if isinstance(result, dict) and result.get("images"):
        return result["images"][0]["url"]
    raise Exception(f"No image returned: {result}")


def download_image(url: str, filepath: Path):
    response = httpx.get(url, timeout=90)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("THEODORE'S WORLD — AI Image Generator")
    log(f"Total images: {len(DELIVERABLES)}")
    log(f"Output folder: {OUTPUT_FOLDER}")
    log("=" * 60)

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # Step 1 — Analyze Theodore's real face once
    theo_face_desc = analyze_theo_face(client)

    # Step 2 — Generate every image
    completed = 0
    skipped   = 0
    failed    = 0

    for i, item in enumerate(DELIVERABLES, 1):
        filepath = OUTPUT_FOLDER / item["filename"]

        if filepath.exists():
            log(f"[{i}/{len(DELIVERABLES)}] SKIP (exists): {item['filename']}")
            skipped += 1
            continue

        log(f"\n[{i}/{len(DELIVERABLES)}] Generating: {item['filename']}")
        log(f"  Character: {item['character']}")

        try:
            # Claude writes the prompt
            log("  Claude writing prompt...")
            hf_prompt = build_higgsfield_prompt(item, theo_face_desc, client)
            log(f"  Prompt: {hf_prompt[:100]}...")

            # Higgsfield generates the image
            log("  Higgsfield generating...")
            image_url = generate_image(hf_prompt)
            log(f"  URL: {image_url[:80]}...")

            # Download and save
            download_image(image_url, filepath)
            log(f"  SAVED: {item['filename']}")
            completed += 1

            # Small pause between generations to be a good API citizen
            time.sleep(2)

        except Exception as e:
            log(f"  ERROR on {item['filename']}: {e}")
            failed += 1
            # Wait a bit before continuing after error
            time.sleep(5)
            continue

    log("\n" + "=" * 60)
    log(f"COMPLETE — Generated: {completed} | Skipped: {skipped} | Failed: {failed}")
    log(f"Images saved to: {OUTPUT_FOLDER}")
    log("=" * 60)


if __name__ == "__main__":
    main()
