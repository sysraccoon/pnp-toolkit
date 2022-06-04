import itertools
import re
from dataclasses import dataclass, field
from glob import glob
from pdfjam import generate_pdf_by_layout
from structs import PaperSpec, ExpectedImageSpec, Size, Offset, ImageLayout
from utils import mkdir, join_pathes
from multiprocessing import Pool, cpu_count
from typing import List

PAPER_SPECS = {
    "a4": PaperSpec(
        Size(210, 297),
        Offset(*([5]*4)),
    ),
    "a3": PaperSpec(
        Size(297, 420),
        Offset(*([5]*4)),
        # Offset(3.2, 3.2, 3.2, 3.2),
    ),
}

IMAGE_SPECS = {
    "vertical_standard": ExpectedImageSpec(
        Size(63, 88.5),
    ),
    "horizontal_standard": ExpectedImageSpec(
        Size(88.5, 63),
    ),
    "mission_cards": ExpectedImageSpec(
        Size(70.0, 70.0),
    ),
    "award_cards": ExpectedImageSpec(
        Size(50.0, 25.0),
    ),
    "tiles": ExpectedImageSpec(
        Size(38.52, 38.52),
    ),
    "tiles_back": ExpectedImageSpec(
        Size(38.52, 38.52),
        mirror=True
    )
}

@dataclass
class CardType:
    name: str
    image_patterns: List[str]
    image_spec: str
    background_pattern: str = None
    multiple_copies: dict = field(default_factory=dict)


CARD_TYPES = [
    CardType("projects", ["Cards - 6,35 x 8,90/Projects*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Project back.png"),
    CardType("preludes", ["Cards - 6,35 x 8,90/Preludes*/*.png"], "horizontal_standard", background_pattern="Cards - 6,35 x 8,90/Prelude back.png"),
    CardType("corporations", ["Cards - 6,35 x 8,90/Corporations*/*.png"], "horizontal_standard", background_pattern="Cards - 6,35 x 8,90/Corporation back.png"),
    CardType("crises", ["Cards - 6,35 x 8,90/Crises*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Global Event back.jpg"),
    CardType("infrastructures", ["Cards - 6,35 x 8,90/Infrastructures*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Infrastructures back.png", multiple_copies={
        r"\/asteroid mine": 7,
        r"\/asteroid outpost": 6,
        r"\/auto factory": 5,
        r"\/auto factory": 5,
        r"\/comsat": 7,
        r"\/freighter": 7,
        r"\/hydroponics": 5,
        r"\/navigational beacon": 7,
        r"\/observatory": 5,
        r"\/orbital headquarters": 5,
        r"\/orbital shipyard": 5,
        r"\/powersat": 6,
        r"\/probe": 7,
        r"\/propellant depot": 5,
        r"\/salvage depot": 5,
        r"\/science facility": 5,
        r"\/space habitat": 6,
        r"\/space trading station": 7,
        r"\/weather satellite": 6,
    }),
    CardType("acts", ["Cards - 6,35 x 8,90/*Acts*/*.png"], "horizontal_standard", background_pattern="Cards - 6,35 x 8,90/Acts back.png"),
    CardType("yellow", ["Cards - 6,35 x 8,90/Yellow*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Project back.png"),
    CardType("global", ["Cards - 6,35 x 8,90/*Global Events*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Global Event back.jpg"),
    CardType("factions", ["Cards - 6,35 x 8,90/Factions*/*.png"], "horizontal_standard", background_pattern="Cards - 6,35 x 8,90/Factions  back.png"),
    CardType("postludes", ["Cards - 6,35 x 8,90/Cards*/*.png"], "vertical_standard", background_pattern="Cards - 6,35 x 8,90/Postlude back.png"),
    CardType("party", ["Cards - 6,35 x 8,90/Party*/*.png"], "horizontal_standard", background_pattern="Cards - 6,35 x 8,90/Parties back.png"),
    CardType("missions", ["Cards - 7 x 7/Missions*/*.png"], "mission_cards", background_pattern="Cards - 7 x 7/Mission back.png"),
    CardType("tile_backs", ["Tiles*/*1.png", "Tiles*/*back.png", "Basic tiles*/*1.png"], "tiles_back", multiple_copies={
        # the moon
        r"\/lunar road": 12,
        r"\/lunar mine.\.png": 12,
        r"\/lunar mine urbanization": 8,
        r"\/lunar habitat": 12,
        # basic tiles
        r"\/city.\.png": 6,
        r"\/dome.\.png": 12,
        r"\/greenery.\.png": 6,
        r"\/wilderness.\.png": 12,
        # venus
        r"\/floating array.\.png": 12,
        r"\/gas mine.\.png": 12,
        r"\/venus habitat.\.png": 10,
    }),
    CardType("tile_fronts", ["Tiles*/*2.png", "Tiles*/*front.png", "Basic tiles*/*2.png"], "tiles", multiple_copies={
        # the moon
        r"\/lunar road": 12,
        r"\/lunar mine.\.png": 12,
        r"\/lunar mine urbanization": 8,
        r"\/lunar habitat": 12,
        # basic tiles
        r"\/city.\.png": 6,
        r"\/dome.\.png": 12,
        r"\/greenery.\.png": 6,
        r"\/wilderness.\.png": 12,
        # venus
        r"\/floating array.\.png": 12,
        r"\/gas mine.\.png": 12,
        r"\/venus habitat.\.png": 10,
    }),
    CardType("ocean_tiles", ["Oceans tiles*/ocean*front*.png"], "tiles", background_pattern="Oceans tiles*/ocean*back.png", multiple_copies={
        r"ocean front-22\+": 6,
    }),
    CardType("awards", ["Awards*/*.jpg"], "award_cards"),
    CardType("milestones", ["Milestones*/*.jpg"], "award_cards"),
]

DEST_DIRNAME = "print"

def process_pdf(paper_name, paper_spec, card_type):
    print(f"Generate pdfs for: {card_type.name} on paper {paper_name}")
    image_spec = IMAGE_SPECS[card_type.image_spec]

    image_patterns = card_type.image_patterns
    temp_image_src = [glob(join_pathes("EPIC*", image_pattern)) for image_pattern in image_patterns]
    temp_image_src = sorted(list(set(itertools.chain(*temp_image_src))))
    images_src = []
    for img in temp_image_src:
        for pattern, duplicate_count in card_type.multiple_copies.items():
            if re.match(f".*{pattern}.*", img):
                images_src.extend([img]*duplicate_count)
                break
        else:
            images_src.append(img)

    background_src = None
    if card_type.background_pattern:
        backrgound_path = join_pathes("EPIC*", card_type.background_pattern)
        background_src = glob(backrgound_path)[0]

    image_layout = ImageLayout(
        paper = paper_spec,
        expected_image = image_spec,
    )

    dest_path = join_pathes(DEST_DIRNAME, paper_name, f"{card_type.name}.pdf")
    generate_pdf_by_layout(image_layout, images_src, dest_path, background_src=background_src, mirror_layout=image_spec.mirror)


def main():
    mkdir(DEST_DIRNAME)

    pool = Pool(cpu_count()//2)

    for paper_name, paper_spec in PAPER_SPECS.items():
        mkdir(join_pathes(DEST_DIRNAME, paper_name))

        for card_type in CARD_TYPES:
            pool.apply_async(process_pdf, (paper_name, paper_spec, card_type))
            

    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
