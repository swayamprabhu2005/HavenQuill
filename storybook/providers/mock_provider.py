"""Mock AI Provider for local, offline, test, and demonstration use."""

from typing import Optional, List, Dict, Any

from storybook.providers.base import BaseAIProvider
from storybook.models import (
    StoryDevelopmentResponse,
    OutlineResponse,
    OutlineChapterProposal,
    SceneBreakdownResponse,
    SceneProposal,
    StoryBibleExtractionResponse,
    CharacterExtraction,
    LocationExtraction,
    CanonFactExtraction,
    ContinuityReviewResponse,
    ContinuityIssue,
    SceneRewriteResponse,
)


class MockProvider(BaseAIProvider):
    """
    Mock AI Provider that operates 100% offline without any API keys or network calls.
    Generates deterministic, schema-compliant sample story content.
    """

    def __init__(self, model_name: str = "mock-story-engine-v1"):
        self.model_name = model_name

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return self.model_name

    def test_connection(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "provider": "mock",
            "model": self.model_name,
            "message": "Mock Provider is active and fully functional offline (no API key required).",
        }

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        prompt_lower = prompt.lower()
        sys_lower = (system_instruction or "").lower()

        if "screenplay" in prompt_lower or "script" in prompt_lower or "screenplay" in sys_lower:
            return (
                "FADE IN:\n\n"
                "INT. GRAND ARCHIVE - NIGHT\n\n"
                "Rain taps rhythmically against high arched stained-glass windows.\n"
                "ELENA VANCE (30s), wearing an oil-stained apron, inspects a brass chronometer.\n\n"
                "ELENA\n"
                "(whispering)\n"
                "The gears shouldn't move counter-clockwise. Unless...\n\n"
                "A distant heavy iron door SLAMS. Footsteps echo on cobblestone.\n\n"
                "SILAS (O.S.)\n"
                "Elena! Put that down. They've crossed the courtyard perimeter.\n\n"
                "Elena quickly pockets the device and turns toward the shadows.\n\n"
                "CUT TO:\n\n"
                "INT. UNDERCITY TUNNEL - CONTINUOUS\n\n"
                "Steam billows from rusted iron valves. Elena and Silas sprint through knee-deep water.\n\n"
                "ELENA\n"
                "How far to the secondary sluice gate?\n\n"
                "SILAS\n"
                "Two hundred yards. If the pressure holds!\n\n"
                "FADE OUT."
            )

        return (
            "[Mock Provider Output]\n"
            "The ancient clocktower struck midnight as the rain drummed softly against the glass. "
            "Elena adjusted her leather satchel and stepped into the dim archive, knowing that the secret "
            "she sought had remained hidden for over three centuries."
        )

    def generate_story_development(
        self, premise: str, genre: str, tone: str, audience: str, notes: str
    ) -> StoryDevelopmentResponse:
        title_hint = premise[:30] if premise else "The Forgotten Chronograph"
        return StoryDevelopmentResponse(
            logline=f"[Mock] When an archivist uncovers a forbidden mechanical relic, she must outrun an imperial guild before the timeline unravels.",
            short_synopsis=f"[Mock] In a clockwork metropolis, Elena Vance discovers an artifact that can record lost moments in history. Hunted by the Iron Synod, she teams up with a rogue engineer to restore the forgotten truth of the city's founding.",
            detailed_synopsis=(
                f"[Mock Detailed Synopsis]\n"
                f"Act I: Elena Vance works quietly in the Grand Archive. While repairing an antique ledger, she finds a hidden brass mechanism. The artifact activates, revealing a coded transmission from her mentor who vanished ten years ago.\n"
                f"Act II: The Iron Synod raids the archive. Elena flees into the Undercity where she meets Silas Rook, an exiled chronometer smith. Together they decode the artifact's coordinates, navigating underground aqueducts and surviving clockwork hounds.\n"
                f"Act III: At the Heart of the Spire, Elena confronts Inquisitor Sterling. Rather than destroying the machine, she broadcasts the preserved history across every church bell in the capital, breaking the Synod's monopoly on the truth."
            ),
            themes=["Preservation of Truth", "Cost of Innovation", "Found Family", "Memory vs. Authority"],
            main_conflict="Elena's duty to expose suppressed history clashes with the Iron Synod's ruthless preservation of social order.",
            main_character_goals=[
                "Elena Vance: Uncover the fate of her mentor and protect the chronograph.",
                "Silas Rook: Clear his family's disgraced name and survive the purge.",
                "Inquisitor Sterling: Retrieve the relic and silence witnesses to maintain order."
            ],
            major_turning_points=[
                "Elena discovers the hidden brass chronograph inside the archival vault.",
                "The Iron Synod burns the lower library, forcing Elena into the subterranean undercity.",
                "Silas reveals the chronograph is not a weapon, but an unalterable recorder of historical truth.",
                "The infiltration of the Grand Clocktower during the Festival of the Solstice."
            ],
            proposed_ending="The true historical records are broadcast across the city bells; the Synod dissolves, and Elena establishes an open, community-led archive.",
            open_questions=[
                "Did Elena's mentor willingly sacrifice himself to seal the vault?",
                "What power source keeps the chronograph functional without winding?",
                "Can Silas reconcile with his estranged sister who works for the city guard?"
            ],
            assumptions=[
                "Assumed the setting combines gaslamp atmospheric details with intricate mechanical steampunk aesthetics.",
                "Assumed magic is absent; the wondrous phenomena arise from lost clockwork science.",
                "Assumed the story is targeted at a general fiction and speculative fiction audience."
            ]
        )

    def generate_outline(
        self, premise: str, synopsis: str, num_chapters: int = 5
    ) -> OutlineResponse:
        chapter_titles = [
            ("The Dust of the Archives", "Elena discovers the hidden chronograph inside an old ledger while archiving forgotten municipal records."),
            ("Fires in the Lower Vaults", "The Iron Synod raids the library; Elena escapes into the misty canals with the help of a mysterious smith."),
            ("The Undercity Workshop", "In Silas's subterranean forge, the chronograph is activated, revealing a recorded memory of the Great Betrayal."),
            ("Ascent of the Spire", "Elena and Silas infiltrate the Central Clocktower disguised as festival repairmen during the annual Solstice celebration."),
            ("The Chiming of Truth", "Elena connects the recorder to the cathedral bells, broadcasting the true history and shattering the Synod's control.")
        ]

        chapters = []
        for i, (title, summary) in enumerate(chapter_titles[:num_chapters], start=1):
            chapters.append(
                OutlineChapterProposal(
                    order_index=i,
                    title=f"Chapter {i}: {title}",
                    summary=f"[Mock] {summary}",
                    character_arcs=[f"Elena faces her reluctance to take risks (Chapter {i})"],
                    turning_points=[f"Key revelation or confrontation occurring in Chapter {i}"],
                    important_revelations=[f"Clue regarding the artifact's true purpose (Chapter {i})"],
                    setup_and_payoff=[f"Setup in early scenes pays off in Chapter {i}"],
                    proposed_resolution=f"Chapter {i} concludes with a dramatic shift toward the climax."
                )
            )

        return OutlineResponse(
            chapters=chapters,
            overall_arc="[Mock] A five-act narrative tracing Elena's journey from isolated scholar to revolutionary chronicler."
        )

    def generate_scene_breakdown(
        self, chapter_title: str, chapter_summary: str, num_scenes: int = 3
    ) -> SceneBreakdownResponse:
        sample_scenes = [
            SceneProposal(
                order_index=1,
                title="The Whisper in the Ledger",
                summary="Elena investigates an irregular binding in a 300-year-old municipal ledger, discovering a concealed brass chronometer.",
                purpose="Establish Elena's expertise, the eerie atmosphere of the archives, and introduce the inciting relic.",
                pov="Elena Vance (Third Person Limited)",
                location="The Grand Archive, Vault B",
                time_marker="Late Evening, Rainstorm",
                characters_present=["Elena Vance"],
                dramatic_conflict="Elena's curiosity compels her to pry open the binding despite archive regulations forbidding alteration.",
                emotional_shift="Mundane boredom shifts to breathless discovery and anxiety.",
                continuity_dependencies=["Ledger inventory number 404-B must match archive records"],
                scene_prose=(
                    "[Mock Prose] The scent of dried parchment and beeswax hung heavy in Vault B. "
                    "Elena traced her thumb along the spine of the ancient tax register, feeling the subtle give "
                    "of hidden hollows where solid board should have been. With a practiced twist of her bone folder, "
                    "she parted the buckram. A soft golden gleam caught the lantern light."
                ),
                camera_framing="Close-up on hands with bone folder, cutting to medium profile shot showing dim vaulted arches.",
                mood_atmosphere="Intimate, dusty, suspenseful, warm amber lantern glow against cold stone shadows.",
                visual_summary="A young archivist with braided auburn hair holds an intricate brass pocket device glowing with tiny gears inside a dark book-lined vault."
            ),
            SceneProposal(
                order_index=2,
                title="Footsteps on the Iron Stairs",
                summary="Heavy boots echo above as Synod hounds arrive early for their inspection; Elena scrambles to conceal her discovery.",
                purpose="Inject immediate tension and force Elena to flee her comfortable sanctuary.",
                pov="Elena Vance",
                location="The Archival Spiral Staircase",
                time_marker="Midnight",
                characters_present=["Elena Vance", "Inquisitor Sterling"],
                dramatic_conflict="Elena must slip past armed guards without triggering the acoustic warning bells.",
                emotional_shift="Curiosity escalates into sharp adrenaline and dread.",
                continuity_dependencies=["Elena must pocket the device before the lantern is extinguished"],
                scene_prose=(
                    "[Mock Prose] The metal treads rang with the cadence of iron-shod boots. "
                    "Elena doused the oil wick with two fingers, plunging the mezzanine into pitch blackness. "
                    "Below, a circle of cold electric torchlight swept the shelves. 'Search every bay,' Sterling's "
                    "voice grated against the iron rafters. 'Nothing leaves this room.'"
                ),
                camera_framing="High-angle downward view through spiral iron railings, casting harsh slatted shadows.",
                mood_atmosphere="Chilling, industrial, high-contrast chiaroscuro, cold blue electric light piercing amber dark.",
                visual_summary="A woman in dark wool coat presses against a bookshelf in shadow as harsh flashlight beams sweep the iron staircase below."
            ),
            SceneProposal(
                order_index=3,
                title="Into the Waterway",
                summary="Elena slips through the coal chute into the canal sluice, escaping into the fog-shrouded river district.",
                purpose="Conclude the chapter with a physical threshold crossing into the dangerous underbelly of the city.",
                pov="Elena Vance",
                location="Low Tide Canal District",
                time_marker="01:00 AM",
                characters_present=["Elena Vance", "Silas Rook"],
                dramatic_conflict="Surviving the freezing canal waters and navigating unfamiliar rogue territory.",
                emotional_shift="Terror transitions into cautious survival and unexpected alliance.",
                continuity_dependencies=["Elena's satchel is waterproofed, preserving the device"],
                scene_prose=(
                    "[Mock Prose] The river air hit her like a wet towel. Elena emerged onto the slime-slicked "
                    "timbers of the lower wharf, shivering violently. A gruff voice materialized from beneath an overturned skiff: "
                    "'If you're looking for the ferryman, miss, you're three hours late and twenty guards short.' "
                    "Silas Rook stood up, tossing an oily rag aside."
                ),
                camera_framing="Wide atmospheric cinematic shot of foggy canal docks with silhouette of a figure holding a lantern.",
                mood_atmosphere="Murky, damp, cobblestone reflections, dense river fog, mysterious.",
                visual_summary="A wet, breathless woman on a foggy wooden dock faces a tall bearded mechanic wearing leather welding apron and grease stains."
            )
        ]

        return SceneBreakdownResponse(
            chapter_id=None,
            chapter_title=chapter_title,
            scenes=sample_scenes[:num_scenes]
        )

    def draft_scene_prose(
        self, scene: SceneProposal, context: str, instructions: str = ""
    ) -> str:
        prose_parts = [
            f"[Mock Generated Prose for: {scene.title}]",
            f"Location: {scene.location or 'The City'} | Time: {scene.time_marker or 'Night'}",
            "",
            f"The silence was broken only by the steady murmur of the surrounding world. "
            f"{scene.summary}",
            "",
            f"Elena hesitated, her fingers brushing the brass contours of the mechanism. "
            f"Every instinct told her to turn back, yet the weight of what she had discovered pulled her onward. "
            f"'{scene.dramatic_conflict}', she thought, knowing that once this threshold was crossed, "
            f"the quiet life of the archives was lost forever.",
            "",
            f"In the distance, the bells chimed, echoing across the rooftops like an ominous promise."
        ]
        if instructions:
            prose_parts.append(f"\n[Applied Creative Instruction: {instructions}]")
        return "\n".join(prose_parts)

    def rewrite_scene(
        self, scene_prose: str, instructions: str, tone: str = ""
    ) -> SceneRewriteResponse:
        return SceneRewriteResponse(
            rewritten_prose=(
                f"[Mock Rewritten Prose - Tone: {tone or 'Enhanced'}]\n"
                f"{scene_prose}\n\n"
                f"[Enhanced with focused sensory detail, tighter pacing, and heightened thematic resonance according to instruction: '{instructions}']"
            ),
            summary_of_changes=f"Strengthened descriptive sensory language and aligned character voice with instruction: '{instructions}'."
        )

    def extract_story_bible(self, text: str) -> StoryBibleExtractionResponse:
        return StoryBibleExtractionResponse(
            characters=[
                CharacterExtraction(
                    canonical_name="Elena Vance",
                    aliases=["The Archivist", "Little Scribe"],
                    description="Junior archivist at the Grand Imperial Archives with a photographic memory and deep expertise in historical binding techniques.",
                    traits=["Meticulous", "Guarded", "Inquisitive", "Courageous under pressure"],
                    relationships={"Silas Rook": "Reluctant ally and mechanical advisor", "Inquisitor Sterling": "Relentless pursuer"}
                ),
                CharacterExtraction(
                    canonical_name="Silas Rook",
                    aliases=["The Clocksmith", "Rook"],
                    description="Former guild engineer cast out of the Iron Synod for questioning official chrono-doctrine.",
                    traits=["Cynical", "Ingenious", "Protective", "Disillusioned"],
                    relationships={"Elena Vance": "Protective ally"}
                ),
                CharacterExtraction(
                    canonical_name="Inquisitor Sterling",
                    aliases=["The Iron Hand"],
                    description="Senior enforcer of the Iron Synod, tasked with suppressing unauthorized knowledge.",
                    traits=["Cold", "Dogmatic", "Methodical", "Unforgiving"],
                    relationships={"Elena Vance": "Fugitive target"}
                )
            ],
            locations=[
                LocationExtraction(
                    name="The Grand Archive",
                    description="A multi-tiered gothic cathedral filled with miles of steel shelving, parchment vaults, and pneumatic message tubes.",
                    rules=["Silence strictly enforced", "Vault B requires double-key clearance", "No open flames allowed"]
                ),
                LocationExtraction(
                    name="The Lower Waterways",
                    description="A maze of subterranean canals and abandoned sewers beneath the city where outlaws and unlicensed tinkerers operate.",
                    rules=["Tides rise rapidly at night", "Watch for steam-pipe vents"]
                )
            ],
            canon_facts=[
                CanonFactExtraction(
                    category="world",
                    subject="The Great Betrayal",
                    fact_text="Three hundred years ago, the city founders erased 40 years of civil war from all public records.",
                    is_locked=True
                ),
                CanonFactExtraction(
                    category="rule",
                    subject="The Chronograph Mechanism",
                    fact_text="The brass chronograph operates on kinetic oscillation and records verbatim acoustic memories directly onto crystallized quartz dials.",
                    is_locked=True
                )
            ]
        )

    def review_continuity(
        self, story_bible_facts: List[str], scene_summaries: List[str]
    ) -> ContinuityReviewResponse:
        return ContinuityReviewResponse(
            summary="[Mock Review] Overall continuity is strong. Two minor timeline and knowledge dependencies were noted for writer review.",
            consistency_score=92,
            issues=[
                ContinuityIssue(
                    category="character_knowledge",
                    severity="low",
                    description="In Scene 2, Elena mentions the name 'Inquisitor Sterling' before he introduces himself or shows credentials.",
                    related_entities=["Elena Vance", "Inquisitor Sterling"],
                    suggested_fix="Have Elena recognize the crest on his uniform instead of speaking his name aloud."
                ),
                ContinuityIssue(
                    category="timeline_conflict",
                    severity="medium",
                    description="The rainstorm is described as ending abruptly between Scene 1 and Scene 2 within a 15-minute window.",
                    related_entities=["Scene 1", "Scene 2"],
                    suggested_fix="Maintain the background rain or describe it diminishing to a cold drizzle."
                )
            ]
        )
