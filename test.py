# -*- coding: utf-8 -*-

import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
# POPRAWKA 1: Dodany import A4
from reportlab.lib.pagesizes import A4

def generuj_umowe_pdf(nazwa_pliku="Umowa_NDA.pdf"):
    """
    Funkcja generuje dokument PDF na podstawie tekstu umowy.
    
    Argumenty:
        nazwa_pliku (str): Nazwa wyjściowego pliku PDF.
    """
    
    # --- Konfiguracja dokumentu ---
    doc = SimpleDocTemplate(
        nazwa_pliku,
        # POPRAWKA 2: Użycie stałej A4 zamiast tekstu 'A4'
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # --- Czcionki ---
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        FONT_NAME = 'DejaVuSans'
        FONT_BOLD_NAME = 'DejaVuSans-Bold'
    except IOError:
        print("Ostrzeżenie: Nie znaleziono czcionek DejaVu. Używam czcionek standardowych.")
        FONT_NAME = 'Helvetica'
        FONT_BOLD_NAME = 'Helvetica-Bold'
        
    # --- Definicje stylów akapitów ---
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleStyle', fontName=FONT_BOLD_NAME, fontSize=14, alignment=TA_CENTER, spaceAfter=16))
    styles.add(ParagraphStyle(name='HeadingStyle', fontName=FONT_BOLD_NAME, fontSize=11, alignment=TA_CENTER, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name='SubHeadingStyle', fontName=FONT_BOLD_NAME, fontSize=11, alignment=TA_LEFT, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='BodyStyle', fontName=FONT_NAME, fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name='IndentStyle', parent=styles['BodyStyle'], leftIndent=20))
    styles.add(ParagraphStyle(name='SignatureTitleStyle', parent=styles['HeadingStyle'], spaceBefore=50))
    styles.add(ParagraphStyle(name='SignatureTextStyle', fontName=FONT_NAME, fontSize=10, alignment=TA_CENTER))

    # --- Treść dokumentu podzielona na sekcje ---
    content_sections = [
        ("WZAJEMNA UMOWA O ZACHOWANIU POUFNOŚCI", "TitleStyle"),
        ("Zawarta w dniu 21.08.2025 pomiędzy:", "BodyStyle"),
        ("<b>1. Stroną A:</b><br/>Ignacym Manturewiczem<br/>zamieszkałym na ul. Wrocławska 82A, Gdynia, 81-530, Polska<br/>PESEL: 04311402274<br/>zwanym dalej „Stroną”,", "BodyStyle"),
        ("a", "BodyStyle"),
        ("<b>2. Stroną B:</b><br/>RESERVMI sp. z o.o.<br/>z siedzibą na ul. Lęborska 3B, Gdańsk, 80-386, Polska<br/>NIP: 9571118484<br/>Numer KRS: 0000802910<br/>Wysokość kapitału zakładowego: 5 000,00zł<br/>reprezentowanym/ą przez: Tomasza Margalskiego,<br/>zwanym/ą dalej „Stroną”,", "BodyStyle"),
        ("zwanymi dalej łącznie „Stronami”.", "BodyStyle"),
        ("PREAMBUŁA", "HeadingStyle"),
        ("Zważywszy, że Strony zamierzają prowadzić rozmowy i negocjacje dotyczące potencjalnej współpracy biznesowej w zakresie integracji inteligentnych systemów obsługi klienta z serwisem rezerwacji Kręgielnia 24 (dalej jako „Cel”), i w związku z tym będą ujawniać sobie wzajemnie informacje poufne, Strony postanawiają zawrzeć niniejszą Umowę o zachowaniu poufności (dalej jako „Umowa”).", "BodyStyle"),
        ("§ 1. Definicja Informacji Poufnych", "SubHeadingStyle"),
        ("Dla celów niniejszej Umowy, „Informacje Poufne” oznaczają wszelkie informacje techniczne, technologiczne, handlowe, finansowe, prawne, organizacyjne i inne, posiadające wartość gospodarczą, ujawnione przez jedną Stronę (zwaną „Stroną Ujawniającą”) drugiej Stronie (zwanej „Stroną Otrzymującą”) w formie pisemnej, ustnej, elektronicznej lub innej, w związku z realizacją Celu.<br/><br/>Informacje Poufne obejmują w szczególności: pomysły, strategie, procesy biznesowe, dane finansowe, listy klientów i kontrahentów, strategie marketingowe, know-how, prototypy, projekty, oprogramowanie, a także sam fakt prowadzenia rozmów między Stronami.<br/><br/>Informacje Poufne nie obejmują informacji, które:", "BodyStyle"),
        ("a) są lub stały się publicznie znane w sposób inny niż poprzez naruszenie niniejszej Umowy przez Stronę Otrzymującą;", "IndentStyle"),
        ("b) były w posiadaniu Strony Otrzymującej przed ich ujawnieniem przez Stronę Ujawniającą, co może być udokumentowane;", "IndentStyle"),
        ("c) zostały ujawnione Stronie Otrzymującej przez osobę trzecią, która nie była zobowiązana do zachowania ich poufności;", "IndentStyle"),
        ("d) muszą zostać ujawnione na podstawie bezwzględnie obowiązujących przepisów prawa lub prawomocnego orzeczenia sądu.", "IndentStyle"),
        ("§ 2. Zobowiązanie do zachowania poufności", "SubHeadingStyle"),
        ("Każda ze Stron zobowiązuje się do zachowania w ścisłej tajemnicy wszelkich Informacji Poufnych otrzymanych od drugiej Strony.<br/><br/>Strona Otrzymująca zobowiązuje się wykorzystywać Informacje Poufne wyłącznie w celu realizacji Celu określonego w preambule.<br/><br/>Strona Otrzymująca zobowiązuje się do ochrony Informacji Poufnych z należytą starannością, nie mniejszą niż ta, z jaką chroni własne informacje poufne.<br/><br/>Ujawnienie Informacji Poufnych pracownikom lub doradcom Strony Otrzymującej może nastąpić jedynie w zakresie, w jakim jest to niezbędne do realizacji Celu i pod warunkiem, że osoby te zostaną zobowiązane do zachowania poufności na warunkach nie mniej restrykcyjnych niż określone w niniejszej Umowie.", "BodyStyle"),
        ("§ 3. Czas trwania obowiązku poufności", "SubHeadingStyle"),
        ("Obowiązek zachowania poufności określony w niniejszej Umowie obowiązuje przez czas trwania współpracy Stron oraz przez okres 3 lat po jej zakończeniu lub po zakończeniu negocjacji, w zależności od tego, co nastąpi później.", "BodyStyle"),
        ("§ 4. Zwrot Informacji Poufnych", "SubHeadingStyle"),
        ("Na pisemne żądanie Strony Ujawniającej, Strona Otrzymująca niezwłocznie zwróci wszelkie materiały zawierające Informacje Poufne lub, na życzenie Strony Ujawniającej, trwale je zniszczy i przedstawi pisemne oświadczenie potwierdzające zniszczenie.", "BodyStyle"),
        ("§ 5. Kara umowna", "SubHeadingStyle"),
        ("W przypadku naruszenia przez jedną ze Stron obowiązku zachowania poufności określonego w § 2, Strona naruszająca zobowiązana będzie do zapłaty na rzecz drugiej Strony kary umownej w wysokości 10 000 PLN (słownie: dziesięć tysięcy złotych) za każdy przypadek naruszenia.<br/><br/>Zapłata kary umownej nie wyłącza prawa Strony poszkodowanej do dochodzenia odszkodowania uzupełniającego na zasadach ogólnych, jeżeli szkoda przewyższa wysokość zastrzeżonej kary umownej.", "BodyStyle"),
        ("§ 6. Postanowienia końcowe", "SubHeadingStyle"),
        ("Wszelkie zmiany niniejszej Umowy wymagają formy pisemnej pod rygorem nieważności.<br/><br/>W sprawach nieuregulowanych niniejszą Umową zastosowanie mają przepisy prawa polskiego, w szczególności Kodeksu Cywilnego.<br/><br/>Wszelkie spory wynikające z niniejszej Umowy będą rozstrzygane przez sąd powszechny właściwy dla siedziby Strony B.<br/><br/>Umowę sporządzono w dwóch jednobrzmiących egzemplarzach, po jednym dla każdej ze Stron.", "BodyStyle"),
        ("PODPISY STRON", "SignatureTitleStyle")
    ]
    
    # --- Budowanie dokumentu ---
    story = []
    for text, style_name in content_sections:
        story.append(Paragraph(text, styles[style_name]))

    # --- Sekcja z podpisami (użycie tabeli dla idealnego wyrównania) ---
    signature_data = [
        [
            Paragraph(".....................................................", styles['SignatureTextStyle']),
            Paragraph(".....................................................", styles['SignatureTextStyle'])
        ],
        [
            Paragraph("<b>Strona A</b>", styles['SignatureTextStyle']),
            Paragraph("<b>Strona B</b>", styles['SignatureTextStyle'])
        ],
        [
            Paragraph("(Ignacy Manturewicz)", styles['SignatureTextStyle']),
            Paragraph("(Tomasz Margalski, Prezes Zarządu)", styles['SignatureTextStyle'])
        ]
    ]
    
    sig_table = Table(signature_data, colWidths=[doc.width/2.0, doc.width/2.0])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(Spacer(1, 1.5*cm))
    story.append(sig_table)
    
    # --- Zapis pliku PDF ---
    try:
        doc.build(story)
        print(f"✅ Sukces! Dokument PDF został zapisany jako '{nazwa_pliku}'")
    except Exception as e:
        print(f"❌ Wystąpił błąd podczas generowania pliku PDF: {e}")

# --- Uruchomienie skryptu ---
if __name__ == '__main__':
    generuj_umowe_pdf()