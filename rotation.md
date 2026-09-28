## Spiegazione Dettagliata ADDON (rotazione in REVITT)

- Cosa fa il modulo **revit_shift_detect.py**

1. **Legge i bounds della nuvola** (il rettangolo verde nell'immagine)
2. **Calcola le dimensioni X e Y** della BBX
3. **Determina quale asse è dominante** (se la BBX è più larga che alta o vice versa)
4. **Calcola l'angolo di rotazione necessario** affinché la **parete rossa (struttura) rimanga parallela ai lati della BBX**

**Esempio bbx in CloudCompare, bbx in giallo e parete selezionata tramite evidenziazione**

- La **BBX** è il rettangolo verde (limiti della nuvola)
- La **parete rossa** è la struttura visibile
- Il valore calcolato è l'angolo da applicare in Revit per far **diventare la parete PARALLELA ai bordi della BBX**

- Visivamente:

# PRIMA della rotazione:
┌─────────────────┐
│   BBX           │
│  ┌─────────┐    │  <- La parete (rossa) e' STORTA rispetto ai bordi
│  │ ┌─┐ __/     │
│  │ │P└─┘/      │
│  │ │A  /       │
│  │ │RETE       │
└─────────────────┘

# DOPO la rotazione (applicando il valore):
┌─────────────────┐
│   BBX           │
│ ┌─────────────┐ │  <- La parete (rossa) e' PARALLELA ai bordi
│ │   PARETE    │ │
│ │             │ │
│ │             │ │
└─────────────────┘