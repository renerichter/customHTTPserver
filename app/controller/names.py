from random import sample
from typing import List, Optional


class CreativeNamer:
    def __init__(self,adjectives:Optional[List[str]]=None,nouns:Optional[List[str]]=None):
        self.adjectives = adjectives if adjectives else self.get_default_adjectives()
        self.nouns = nouns if nouns else self.get_default_nouns()
    
    def get_default_adjectives(self):
        return ['radiant', 'effervescent', 'luminous', 'whimsical', 'vibrant', 'ebullient', 'majestic', 'mystical', 'fantastical', 'celestial', 'galvanizing', 'brilliant', 'miraculous', 'otherworldly', 'resplendent', 'stellar', 'serendipitous', 'electrifying', 'enchanting', 'iridescent']

    def get_default_nouns(self):
        return ["Unicorn", "Supernova", "Black Hole", "Quasar", "Nebula", "Photon", "Comet", "Star", "Galaxy", "Meteorite", "Aurora", "Wormhole", "Rainbow", "Pulsar", "Exoplanet", "Tesseract", "Dark Matter", "Moonstone", "Asteroid", "Solar Flare"]

    def create_name(self,nbr_adjectives:int=1):
        adj=" ".join(sample(self.adjectives,nbr_adjectives))
        noun = sample(self.nouns,1)[0]
        return f"{adj} {noun}" 
    
    def create_many_names(self,nbr_names:int,nbr_adjectives:int=1):
        list_of_names = [self.create_name(nbr_adjectives) for _ in range(nbr_names)]
        return list_of_names