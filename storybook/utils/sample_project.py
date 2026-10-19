"""Seeds a clearly labeled fictional demonstration project into the local database."""

import logging
from storybook.models import Project, Chapter, Scene, Character, Location, CanonFact, SourceDraft
from storybook.repositories import (
    ProjectRepository,
    ChapterRepository,
    SceneRepository,
    StoryBibleRepository,
    SourceDraftRepository,
)

logger = logging.getLogger(__name__)

SAMPLE_PROJECT_ID = "fictional-sample-clockwork-archivist"


def seed_sample_project_if_needed() -> Project:
    """Ensure a rich fictional sample project exists for immediate demonstration."""
    proj_repo = ProjectRepository()
    existing = proj_repo.get(SAMPLE_PROJECT_ID)
    if existing:
        return existing

    # Create Sample Project
    project = Project(
        id=SAMPLE_PROJECT_ID,
        title="[SAMPLE] The Clockwork Archivist",
        subtitle="A Gaslamp Fantasy of Hidden Time",
        genre="Gaslamp Steampunk Fantasy",
        tone="Atmospheric, Intriguing, and Cinematic",
        language="English",
        intended_audience="Adult / Speculative Fiction Readers",
        premise=(
            "When junior archivist Elena Vance discovers an illegal brass chronograph hidden inside "
            "a municipal tax register, she discovers that forty years of the city's history were deliberately erased. "
            "Teaming up with an outcast clocksmith, she must broadcast the recorded truth before the Iron Synod "
            "silences her forever."
        ),
        synopsis=(
            "In the fog-laden metropolis of Oakhaven, history is strictly regulated by the Iron Synod. "
            "Elena Vance discovers a forbidden clockwork device that records memories directly into quartz crystal. "
            "When her archives are raided, Elena flees into the subterranean canals where she joins forces with Silas Rook. "
            "Together they race against Inquisitor Sterling to ascend the Great Clocktower and broadcast the suppressed past."
        ),
        metadata_json={
            "is_sample": True,
            "sample_label": "Official Fictional Demo Project",
            "last_provider": "mock",
        }
    )
    proj_repo.create(project)

    # Add Source Draft
    draft_repo = SourceDraftRepository()
    draft_repo.create(
        SourceDraft(
            project_id=SAMPLE_PROJECT_ID,
            source_type="typed",
            original_text=(
                "Rough initial notes: A young woman working in a high-vaulted library finds a strange device "
                "hidden within an old ledger. The device doesn't tell the time—it preserves sounds and memories. "
                "The city church considers this forbidden heresy."
            ),
        )
    )

    # Chapters & Scenes
    ch_repo = ChapterRepository()
    sc_repo = SceneRepository()

    # Chapter 1
    ch1 = ch_repo.create(
        Chapter(
            project_id=SAMPLE_PROJECT_ID,
            order_index=1,
            title="Chapter 1: The Whispering Vault",
            summary="Elena discovers the brass chronograph during late-night archival repairs and flees an inspection.",
            status="completed",
        )
    )
    sc_repo.create(
        Scene(
            chapter_id=ch1.id,
            order_index=1,
            title="The Buckram Binding",
            summary="Elena discovers the hidden cavity inside Ledger 404-B.",
            prose=(
                "The smell of dried buckram and aged cedar was the only constant Elena Vance trusted. "
                "Beneath the vaulted stone of Vault B, three storeys below the soot-stained cobblestones of Oakhaven, "
                "she slid her bone folder along the inner hinge of the municipal tax registry from the Year of the Eclipse.\n\n"
                "The spine gave way with a crisp, hollow click. Not the brittle snap of decaying vellum, but the precision "
                "give of oiled gears. Resting inside the carved cavity was a device no larger than a pocket watch, "
                "its casing fashioned from hammered brass and etched with concentric rings of celestial numerals."
            ),
            pov="Elena Vance",
            location_name="Vault B, Grand Archive",
            time_marker="Late Evening",
            characters_present=["Elena Vance"],
            status="completed",
            camera_framing="Macro close-up on delicate fingers parting vellum, revealing brass gears glowing under lantern light.",
            mood_atmosphere="Quiet, scholarly, dusty amber illumination against cavernous stone vaults.",
            visual_summary="A young archivist with braided auburn hair holds an intricate brass pocket device inside a dark gothic library vault."
        )
    )
    sc_repo.create(
        Scene(
            chapter_id=ch1.id,
            order_index=2,
            title="Lanterns on the Iron Grate",
            summary="Inquisitor Sterling's enforcers arrive unexpectedly, forcing Elena to escape into the coal chutes.",
            prose=(
                "The acoustic bells on the ceiling rang once—a sharp, bronze chime that signaled the opening of the upper gates. "
                "Elena froze. No cataloguer was permitted in the stacks after the eighth toll of the cathedral bell.\n\n"
                "Heavy footsteps crunched against the iron walkways above. 'Check the tax series,' a gravel voice echoed. "
                "Inquisitor Sterling. Elena slipped the chronograph into her leather satchel, blew out the whale-oil lamp, "
                "and melted into the shadow behind the pneumatic delivery chutes."
            ),
            pov="Elena Vance",
            location_name="Grand Archive Mezzanine",
            time_marker="11:45 PM",
            characters_present=["Elena Vance", "Inquisitor Sterling"],
            status="completed",
            camera_framing="High-angle shot looking down from iron catwalks, harsh flashlights cutting through swirling dust.",
            mood_atmosphere="Urgent, menacing, shadows punctuated by stark beams of white electric light.",
            visual_summary="An archivist slips into a narrow access tunnel in shadow while armed cloaked figures search above."
        )
    )

    # Chapter 2
    ch2 = ch_repo.create(
        Chapter(
            project_id=SAMPLE_PROJECT_ID,
            order_index=2,
            title="Chapter 2: The Low-Tide Haven",
            summary="Elena reaches the subterranean canal district and meets Silas Rook, an exiled guild clocksmith.",
            status="draft",
        )
    )
    sc_repo.create(
        Scene(
            chapter_id=ch2.id,
            order_index=1,
            title="The Black Wharf",
            summary="Elena emerges from the drainage culvert into the misty canal docks.",
            prose=(
                "The canal water was black as ink, carrying the stench of coal tar and bilge. "
                "Elena tumbled onto the slime-slicked dock timbers, shivering violently in the pre-dawn fog.\n\n"
                "'You're dripping archival paste all over my landing, Vance,' said a voice from the fog. "
                "Silas Rook stood under the rusted archway of his forge, a glowing copper pipe clamped in his teeth. "
                "He glanced at her saturated satchel. 'I take it the Synod didn't approve your reading list.'"
            ),
            pov="Elena Vance",
            location_name="Low-Tide Canal Wharf",
            time_marker="02:30 AM",
            characters_present=["Elena Vance", "Silas Rook"],
            status="completed",
            camera_framing="Atmospheric wide shot of misty Victorian canal dock with silhouette of a tinker by a glowing forge.",
            mood_atmosphere="Damp, murky, amber forge light reflecting on dark greasy water.",
            visual_summary="A woman drenched from a canal canal exit talks to a burly mechanic holding an oil lantern on a foggy wooden pier."
        )
    )

    # Story Bible records
    bible_repo = StoryBibleRepository()

    # Characters
    bible_repo.create_character(
        Character(
            project_id=SAMPLE_PROJECT_ID,
            canonical_name="Elena Vance",
            aliases_json=["The Scribe", "Vance"],
            description="Junior archivist at Oakhaven's Grand Library with rare expertise in medieval codices and chronometry.",
            traits_json=["Methodical", "Brave", "Perceptive", "Reluctant Hero"],
            relationships_json={"Silas Rook": "Trusted mechanic ally", "Inquisitor Sterling": "Mortal enemy"},
            locked_fields_json=["canonical_name", "traits_json"]
        )
    )
    bible_repo.create_character(
        Character(
            project_id=SAMPLE_PROJECT_ID,
            canonical_name="Silas Rook",
            aliases_json=["The Clocksmith"],
            description="Disgraced former guild craftsman operating an unlicensed subterranean forge in the Undercity.",
            traits_json=["Cynical", "Brilliant", "Fiercely loyal", "Grizzled"],
            relationships_json={"Elena Vance": "Protective ally"},
            locked_fields_json=["canonical_name"]
        )
    )
    bible_repo.create_character(
        Character(
            project_id=SAMPLE_PROJECT_ID,
            canonical_name="Inquisitor Sterling",
            aliases_json=["The Steel Hand"],
            description="Lead enforcer of the Iron Synod, ruthless in suppressing forbidden knowledge.",
            traits_json=["Cold", "Dogmatic", "Relentless"],
            relationships_json={"Elena Vance": "Hunted target"},
            locked_fields_json=["canonical_name"]
        )
    )

    # Locations
    bible_repo.create_location(
        Location(
            project_id=SAMPLE_PROJECT_ID,
            name="Grand Archive of Oakhaven",
            description="Massive cathedral-sized repository of all approved civic knowledge, patrolled day and night.",
            rules_json=["Silence mandatory", "Open flames strictly prohibited", "Access restricted after 8 PM"]
        )
    )
    bible_repo.create_location(
        Location(
            project_id=SAMPLE_PROJECT_ID,
            name="The Low-Tide Canals",
            description="Subterranean waterway network beneath Oakhaven where unlicensed tinkerers hide.",
            rules_json=["Tides rise swiftly", "Beware toxic boiler exhaust vents"]
        )
    )

    # Canon Facts (with Locked Canon Facts)
    bible_repo.create_canon_fact(
        CanonFact(
            project_id=SAMPLE_PROJECT_ID,
            category="world",
            subject="The Great Chrono-Erasure",
            fact_text="In the year 1842, the Iron Synod deleted all documentation of the Forty-Day Rebellion.",
            is_locked=True
        )
    )
    bible_repo.create_canon_fact(
        CanonFact(
            project_id=SAMPLE_PROJECT_ID,
            category="technology",
            subject="Quartz Chronographs",
            fact_text="Chronographs store acoustic vibrations inside crystallized quartz and cannot be altered or rewritten.",
            is_locked=True
        )
    )

    return project
