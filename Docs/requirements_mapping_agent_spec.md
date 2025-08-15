# Spezifikation: Requirements-Mapping-Agent

## Überblick
Der Requirements-Mapping-Agent ordnet unstrukturierte Requirements automatisch einer vorgegebenen Dokumentenstruktur zu. Der Agent analysiert Requirements semantisch und platziert sie in passende Kapitel und Unterkapitel einer hierarchischen Dokumentenstruktur.

## Input-Dokumente

### 1. Requirements-Dokument (Input)
- **Format**: JSON
- **Struktur**: Flache Liste von Requirements
- **Pflichtfelder pro Requirement**:
  - `id`: Eindeutige Kennung (z.B. "BR-FUN-001")
  - `title`: Kurzbeschreibung
  - `description`: Detaillierte Anforderungsbeschreibung
  - `category`: Kategorie (z.B. "Functional", "Performance", "Safety")
  - `priority`: Priorität (z.B. "Critical", "High", "Medium", "Low")

### 2. Dokumentenstruktur (Referenz/Ressource)
- **Format**: JSON
- **Struktur**: Hierarchische Dokumentenvorlage mit Kapiteln und Unterkapiteln
- **Pflichtfelder**:
  - `headers`: Array mit Dokumentenstruktur
    - `id`: Eindeutige Heading-ID
    - `title`: Überschrift
    - `outlineNumber`: Gliederungsnummer (z.B. "1.3", "2.1")
    - `type`: "heading"

## Mapping-Prozess

### Phase 1: Strukturanalyse
1. **Dokumentenstruktur verstehen**
   - Hierarchie der Kapitel extrahieren
   - Semantische Bedeutung der Überschriften analysieren
   - Thematische Bereiche identifizieren

2. **Requirements kategorisieren**
   - Inhalt und Kontext jedes Requirements analysieren
   - Schlüsselwörter und Konzepte extrahieren
   - Kategorie und Priorität berücksichtigen

### Phase 2: Semantisches Mapping
1. **Kontextbasierte Zuordnung**
   - Requirements basierend auf inhaltlicher Übereinstimmung zuordnen
   - Folgende Mapping-Regeln anwenden:
     
   **Funktionale Requirements**:
   - Basis-Funktionen → "Summary of the Function" (1.3)
   - Erweiterte Funktionen → "Intended Use" (1.4.1)
   - ABS, Assistenzsysteme → "Intended Use" (1.4.1)

   **Performance Requirements**:
   - Leistungskennzahlen → "Assumptions" (1.4.2)
   - Zeitvorgaben → "Assumptions" (1.4.2)

   **Interface Requirements**:
   - Externe Schnittstellen → "Context & External Interfaces" (2.1)
   - Systemintegration → "Context & External Interfaces" (2.1)

   **Safety Requirements**:
   - Kritische Sicherheitsfunktionen → "Functional Safety Concept/Risk 1" (4.1)
   - Redundanzsysteme → "Functional Safety Concept/Risk 1" (4.1)
   - Monitoring-Funktionen → "Sub-Functions" (2.2)

   **Environmental Requirements**:
   - Betriebsbedingungen → "Operation" (3.1)
   - Umweltbeständigkeit → "Operation" (3.1)

   **Maintenance & Testing Requirements**:
   - Wartung → "Service & Maintenance" (3.4)
   - Tests → "Service & Maintenance" (3.4)

   **Regulatory Requirements**:
   - Compliance, Standards → "Functional Safety Concept/Risk 1" (4.1)
   - Materialvorschriften → "Manufacturing" (3.2)

2. **Konfliktauflösung**
   - Bei mehreren möglichen Zuordnungen: Priorität nach semantischer Nähe
   - Berücksichtigung von Requirement-Kategorie als sekundäres Kriterium

### Phase 3: Strukturierte Ausgabe
1. **Hierarchisches JSON erstellen**
   - Dokumentenstruktur als Rahmen verwenden
   - Requirements in entsprechende Kapitel einsortieren
   - Originalattribute der Requirements beibehalten

2. **Ausgabeformat**:
   ```json
   {
     "document": {
       "id": "...",
       "title": "...",
       "chapters": [
         {
           "heading": "...",
           "heading_id": "...",
           "outlineNumber": "...",
           "workitems": [
             {
               "id": "requirement_id",
               "title": "...",
               "description": "...",
               "category": "...",
               "priority": "..."
             }
           ],
           "subchapters": [...]
         }
       ]
     }
   }
   ```

## Entscheidungslogik

### Primäre Zuordnungskriterien
1. **Semantische Übereinstimmung**: Inhaltliche Nähe zwischen Requirement-Beschreibung und Kapitelüberschrift
2. **Kategoriebasierte Zuordnung**: Requirement-Kategorie als Orientierung
3. **Schlüsselwort-Matching**: Spezifische Begriffe (z.B. "interface" → Interface-Kapitel)

### Sekundäre Kriterien
1. **Priorität**: Kritische Requirements in Safety-relevante Kapitel
2. **Technische Abhängigkeiten**: Zusammengehörige Requirements gruppieren

## Qualitätssicherung

### Validierungsschritte
1. Alle Input-Requirements müssen zugeordnet werden
2. Keine doppelten Zuordnungen (jedes Requirement nur einmal)
3. Strukturelle Integrität der Ausgabe gewährleisten

### Logging
- Zuordnungsentscheidungen dokumentieren
- Konfidenzwerte für Zuordnungen (falls implementiert)
- Nicht zuordenbare Requirements kennzeichnen

## Erweiterbarkeit

### Konfigurierbare Elemente
- Mapping-Regeln als externe Konfiguration
- Anpassbare Schlüsselwortlisten
- Gewichtung der Zuordnungskriterien

### Unterstützte Dokumenttypen
- Aktuell: Functional Concept Templates
- Erweiterbar auf andere strukturierte Dokumentvorlagen
- Flexibles Schema-Mapping

## Implementierungshinweise

Der Agent sollte:
1. Robust gegen Variationen in der Schreibweise sein
2. Kontextinformationen über mehrere Sätze hinweg verstehen
3. Mehrdeutigkeiten explizit behandeln
4. Skalierbar für große Requirement-Mengen sein