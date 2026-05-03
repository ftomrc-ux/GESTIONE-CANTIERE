import math
import numpy as np

class NTC_Calcolatore_Avanzato:
    def __init__(self, zona_v=3, zona_n=2, altitudine=500):
        # Dati sito (Tab. 3.3.I e 3.4.I)
        self.qb = 0.5 * 1.25 * (27**2) / 1000 # Esempio semplificato
        self.qsk = 1.0 # Valore base neve

    def get_coefficiente_esposizione(self, z, categoria='B'):
        """Rif. Tabella 3.3.II - Parametri rugosità[cite: 3]"""
        params = {
            'A': [0.16, 0.01, 2], 'B': [0.19, 0.05, 4], 
            'C': [0.20, 0.10, 5], 'D': [0.22, 0.30, 8], 'E': [0.23, 0.70, 12]
        }
        kr, z0, zmin = params[categoria]
        ze = max(z, zmin)
        return (kr**2) * math.log(ze/z0) * (7 + math.log(ze/z0))

    # --- TIPOLOGIE EDIFICIO (CIRCOLARE 2019) ---
    
    def calcola_rettangolare(self, h, d, b, z, cat):
        """Par. C3.3.10.1 - Edifici a pianta rettangolare[cite: 3]"""
        ce = self.get_coefficiente_esposizione(z, cat)
        cp = 0.8 # Sopravento (Zona D)
        return self.qb * ce * cp

    def calcola_cilindro(self, diametro, z, cat, rugosita=0.5):
        """Par. C3.3.10.10 - Serbatoi e Camini"""
        ce = self.get_coefficiente_esposizione(z, cat)
        vz = 27 * math.sqrt(ce)
        re = (diametro * vz) / 1.5e-5 # Numero di Reynolds
        # Coefficiente di forza cf dipendente da Re (Grafico C3.3.14)
        cf = 0.7 if re > 1e6 else 1.2
        return self.qb * ce * cf

    def calcola_tettoia(self, phi, z, cat):
        """Par. C3.3.10.4 - Tettoie isolante[cite: 3]"""
        ce = self.get_coefficiente_esposizione(z, cat)
        cp_net = 1.2 + 0.3 * phi # Caso massimo ostruzione[cite: 3]
        return self.qb * ce * cp_net

    def calcola_neve_copertura(self, tipo="monofalda", pend=15):
        """Cap. 3.4.3 - Carico Neve[cite: 1]"""
        if pend <= 30: mu = 0.8 # Tab. 3.4.I[cite: 1]
        elif pend < 60: mu = 0.8 * (60 - pend) / 30
        else: mu = 0.0
        return self.qsk * mu

# --- UTILIZZO ---
calc = NTC_Calcolatore_Avanzato()
print(f"Pressione vento su Cilindro a 20m (Cat. B): {calc.calcola_cilindro(5, 20, 'B'):.3f} kN/m2")
print(f"Pressione netta su Tettoia (phi=0.5): {calc.calcola_tettoia(0.5, 5, 'B'):.3f} kN/m2")