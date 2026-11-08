"""
Configuration and tunable parameters for the Kuku Promo Finder.
All thresholds, weights, keyword lists, and model settings live here
so they are easy to inspect, explain, and swap.
"""

# ─── Duration constraints (seconds) ─────────────────────────────────────────
MIN_PROMO_DURATION = 20.0
MAX_PROMO_DURATION = 60.0
IDEAL_DURATION_RANGE = (28.0, 48.0)  # sweet-spot for vertical video retention

# ─── Hook detection window ───────────────────────────────────────────────────
HOOK_WINDOW_SEC = 3.5          # seconds from clip start to search for a hook
HOOK_MIN_SCORE = 1.5           # minimum hook score to keep a candidate at all
HOOK_DECAY_RATE = 0.4          # score penalty per second past 3.0s

# ─── Cliffhanger detection window ────────────────────────────────────────────
CLIFF_WINDOW_SEC = 4.0         # seconds from clip end to search backwards
CLIFF_MIN_SCORE = 1.0          # minimum cliff score to keep a candidate

# ─── Non-Maximum Suppression (NMS) ───────────────────────────────────────────
NMS_IOU_THRESHOLD = 0.35       # Intersection-over-Union threshold for dedup

# ─── Composite scoring weights ───────────────────────────────────────────────
# Must sum to 1.0
WEIGHT_HOOK = 0.30
WEIGHT_CLIFFHANGER = 0.25
WEIGHT_STANDALONE = 0.20
WEIGHT_INTENSITY = 0.15
WEIGHT_CONTEXT = 0.10

# ─── Keywords: hooks ─────────────────────────────────────────────────────────
HOOK_ACTION_KEYWORDS = [
    "slap", "strike", "struck", "grab", "shove", "push", "tear", "rip",
    "kneel", "draws", "unsheathes", "dagger", "sword", "blade", "chains",
    "collar", "shatters", "smashes", "kicks", "blood", "bleeds", "whip",
    "iron", "burn", "collapses", "faints", "gasps", "seizes", "arrest",
    "brandishes", "drags", "blocks", "drives", "rake",
]

HOOK_DIALOGUE_KEYWORDS = [
    "turn around", "cannot marry", "low value", "plainness", "disowned",
    "beggar", "cripple", "broken", "thief", "steal", "stolen", "witch",
    "witchcraft", "poison", "poisoned", "execute", "execution", "die",
    "kill", "bastard", "who gave you permission", "bow", "kneel", "duke",
    "duchess", "imposter", "arrest", "get out", "how dare you", "liar",
    "treason", "adultery", "you are under arrest", "guards",
]

# Premium hook phrases that score very high
PREMIUM_HOOK_PHRASES = [
    "you should turn around", "cannot marry a woman", "low value",
    "plainness", "married a beggar", "you're the duke", "arrest this imposter",
    "guards! arrest", "put out your hands", "you are under arrest",
    "she is a witch", "duchess of ashburton", "broken scrap",
]

# ─── Keywords: cliffhangers ──────────────────────────────────────────────────
CLIFFHANGER_ACTION_KEYWORDS = [
    "cut to black", "freezes", "eyes widen", "gasp", "stares in horror",
    "stares in disbelief", "hand trembling", "blade at", "knuckles whiten",
    "door bursts", "emerges", "shadow looms", "raised high", "about to strike",
    "approaches menacingly",
]

CLIFFHANGER_DIALOGUE_KEYWORDS = [
    "?", "...", "who are you", "what have you done", "unless", "never",
    "you will pay", "my husband", "my wife", "the duke", "true duke",
    "sentence you", "too late", "what is this", "tell me",
]

PREMIUM_CLIFFHANGER_PHRASES = [
    "cut to black", "wife?!", "accept my hand", "this is my son",
    "going to strike", "what is it, soldier", "enough!", "true duke",
    "who gave you permission", "we settle what you stole",
]

# ─── Context and standalone-clarity penalties ────────────────────────────────
HIGH_CONTEXT_JARGON = [
    "charcoal antidote", "council bylaws", "chapter seven",
    "estates committee", "botanical classification", "section four",
    "tithe records", "deed transfer", "matrimonial registry",
]

# Medical/quiet scenes that look dramatic by keyword but aren't
MEDICAL_QUIET_TERMS = [
    "charcoal", "antidote", "grimoire", "remedy journal",
    "fever-stricken", "herbal", "botanical", "tea", "compress",
    "yarrow", "poultice",
]

# Universal archetypes that cold viewers instantly understand
UNIVERSAL_ARCHETYPES = [
    "altar", "wedding", "gown", "bride", "groom", "plainness", "beggar",
    "soldier", "duke", "duchess", "arrest", "imposter", "proposal",
    "chains", "execution", "witch", "poison",
]

# ─── Model / AI configuration (for future LLM integration) ──────────────────
# Set to None to use the keyword-based pipeline only.
# When set, the evaluator will call the model for contextual judgment.
LLM_PROVIDER = None          # "google", "openai", "local", or None
LLM_MODEL_NAME = None        # e.g. "gemini-2.0-flash", "gpt-4o-mini"
LLM_API_KEY_ENV_VAR = None   # name of env var holding the key

# ─── Output paths ────────────────────────────────────────────────────────────
RAW_OUTPUT_DIR = "outputs/raw"
REPORTS_OUTPUT_DIR = "outputs/reports"

