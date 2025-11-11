# quitus_app/pdf_generator.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from datetime import datetime
from io import BytesIO
import qrcode
import os
from typing import Optional

# Chemin vers le logo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "images", "logo", "logo.png")
TUV_LOGO_PATH = os.path.join(BASE_DIR, "TUV.png")

def _build_translucent_logo_png(color: str = "black", alpha: float = 0.12) -> Optional[BytesIO]:
    """Crée un logo filigrane réellement translucide en conservant sa forme.

    Étapes:
    1. Ouvre le logo.
    2. Convertit les zones blanches quasi pures en transparentes pour ne garder que l'emblème.
    3. Applique une teinte (noir ou blanc) avec une opacité globale.
    4. Retourne un PNG RGBA prêt pour le tiling.
    """
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        base = Image.open(LOGO_PATH).convert("RGBA")
        pixels = base.load()
        w, h = base.size
        # Supprimer le fond blanc en le rendant transparent (seuil de luminosité)
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    # si proche du blanc
                    if r > 240 and g > 240 and b > 240:
                        # rendre entièrement transparent
                        pixels[x, y] = (r, g, b, 0)
        # Teinte unie sur la silhouette restante
        a_val = max(0, min(255, int(alpha * 255)))
        if color.lower() == "white":
            tint = (255, 255, 255, a_val)
        else:
            tint = (0, 0, 0, a_val)
        # Applique la teinte en conservant l'alpha (multiplication simple)
        r_channel, g_channel, b_channel, a_channel = base.split()
        tint_img = Image.new("RGBA", base.size, tint)
        out = Image.new("RGBA", base.size, (0, 0, 0, 0))
        out.paste(tint_img, (0, 0), mask=a_channel)
        buf = BytesIO()
        out.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception:
        return None

def generer_qr_code(data):
    """Générer un QR code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_quitus_pdf(quitus):
    """Générer le PDF du quitus selon le modèle officiel"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Couleurs du Port Autonome de Lomé
    bleu_marine = (0/255, 32/255, 96/255)
    jaune = (1, 0.84, 0)
    gris_clair = (0.9, 0.9, 0.9)
    
    # ==================== EN-TÊTE ====================
    # Fond blanc par défaut
    
    # Logo du PAL à gauche (entête) - augmenté en taille
    logo_image = ImageReader(LOGO_PATH)
    logo_header_size = 40*mm  # Augmenté de 30mm à 40mm
    logo_header_x = 15*mm
    # Aligné horizontalement avec REPUBLIQUE TOGOLAISE (height - 15mm)
    header_text_y = height - 15*mm
    # Centrer verticalement le logo par rapport au texte - déplacé légèrement vers le bas
    logo_header_y = header_text_y - (logo_header_size / 2) - 5*mm
    c.drawImage(logo_image, logo_header_x, logo_header_y, width=logo_header_size, height=logo_header_size, mask='auto')
    
    # Texte d'en-tête collé au logo
    header_text = "PORT AUTONOME DE LOME"
    c.setFillColorRGB(*bleu_marine)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(logo_header_x + logo_header_size - 8*mm, header_text_y, header_text)

    # Police manuscrite pour la devise si dispo - commence au niveau du T de PORT
    motto_font_name = "Helvetica-Oblique"
    motto_y = header_text_y - 6*mm
    try:
        # Chercher une police script optionnelle (ex: GreatVibes-Regular.ttf) dans BASE_DIR/fonts
        fonts_dir = os.path.join(BASE_DIR, "fonts")
        possible_fonts = [
            ("GreatVibes", "GreatVibes-Regular.ttf"),
            ("DancingScript", "DancingScript-Regular.ttf"),
            ("Pacifico", "Pacifico-Regular.ttf"),
        ]
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        for fam, fname in possible_fonts:
            font_path = os.path.join(fonts_dir, fname)
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(fam, font_path))
                motto_font_name = fam
                break
    except Exception:
        pass
    c.setFont(motto_font_name, 11)
    c.setFillColorRGB(1, 0.84, 0)  # Couleur jaune
    # Commence au niveau du T (même x que PORT) - déplacé vers la droite de 8mm
    c.drawString(logo_header_x + logo_header_size - 8*mm + 8*mm, motto_y, "La passion de l'efficacité")

    # === FILIGRANE (watermark) : tuile PNG translucide préparée automatiquement ===
    # Prépare une version translucide (noir 5%) du logo conservant sa forme
    wm_buf = _build_translucent_logo_png(color="black", alpha=0.05)
    wm_image = None
    if wm_buf is not None:
        try:
            wm_image = ImageReader(wm_buf)
        except Exception:
            wm_image = None

    # Si la génération a échoué, repli sur l'image originale (plus visible)
    tile_image = wm_image if wm_image is not None else logo_image

    # Paramètres extrêmes demandés: taille 10mm et espacement 1.0x (logos très nombreux)
    wm_size = 10 * mm
    step_x = wm_size * 1.0
    step_y = wm_size * 1.0
    y = 0
    while y < height + wm_size:
        x = -wm_size / 2
        while x < width + wm_size:
            try:
                c.drawImage(tile_image, x, y, width=wm_size, height=wm_size, mask='auto')
            except Exception:
                # ignorer ce tile en cas d'erreur ponctuelle
                pass
            x += step_x
        y += step_y
    
    # (Logo central retiré selon nouvelle directive)
    # Définir une position de titre directement basée sur l'entête - déplacé encore plus vers le haut
    logo_y = height - 30*mm  # Titre à 30mm du haut

    # Texte "REPUBLIQUE TOGOLAISE" en noir à droite
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 10*mm, height - 15*mm, "REPUBLIQUE TOGOLAISE")
    c.setFont("Helvetica-Oblique", 8)
    # "Travail - Liberté - Patrie" déplacé vers la gauche de 7mm, avec "Liberté" souligné
    text_y = height - 20*mm
    text_x = width - 10*mm - 7*mm
    
    # Dessiner le texte complet aligné à droite
    full_text = "Travail - Liberté - Patrie"
    c.drawRightString(text_x, text_y, full_text)
    
    # Calculer les largeurs pour positionner le soulignement sous "Liberté"
    travail_text = "Travail - "
    liberte_text = "Liberté"
    
    travail_width = c.stringWidth(travail_text, "Helvetica-Oblique", 8)
    liberte_width = c.stringWidth(liberte_text, "Helvetica-Oblique", 8)
    full_text_width = c.stringWidth(full_text, "Helvetica-Oblique", 8)
    
    # Position du début du texte (après l'alignement à droite)
    text_start_x = text_x - full_text_width
    
    # Position du soulignement sous "Liberté"
    underline_start_x = text_start_x + travail_width
    underline_end_x = underline_start_x + liberte_width
    underline_y = text_y - 1.5*mm
    c.setLineWidth(0.5)
    c.line(underline_start_x, underline_y, underline_end_x, underline_y)

    # ==================== TITRE PRINCIPAL ====================
    # Placer le titre juste en dessous du logo (petit écart)
    title_y = logo_y - 8*mm
    c.setFont("Helvetica-Bold", 18)  # Taille demandée (18 pt)
    c.drawCentredString(width/2, title_y, "QUITUS PORTUAIRE")

    # Lignes sous le titre - réduites au quart
    c.setLineWidth(1.5)  # Ligne plus fine
    line_width = 18.75*mm  # Quart de 75mm
    c.line(width/2 - line_width, title_y - 2*mm, width/2 + line_width, title_y - 2*mm)
    c.setLineWidth(0.5)
    c.line(width/2 - line_width, title_y - 3*mm, width/2 + line_width, title_y - 3*mm)

    # ==================== QUITUS N° et VALABLE JUSQU'AU ====================
    # Positionner la section principale sous le titre
    y_pos = title_y - 15*mm
    c.setFont("Helvetica-Bold", 10)  # Police réduite
    c.drawString(30*mm, y_pos, "QUITUS N° :")
    c.rect(80*mm, y_pos - 3*mm, 75*mm, 8*mm, fill=0, stroke=1)  # Rectangle plus petit
    c.setFont("Helvetica", 10)
    c.drawString(85*mm, y_pos, str(quitus.numero_quitus))
    
    y_pos -= 10*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30*mm, y_pos, "VALABLE JUSQU'AU :")
    c.rect(80*mm, y_pos - 3*mm, 75*mm, 8*mm, fill=0, stroke=1)
    c.setFont("Helvetica", 10)
    c.drawString(85*mm, y_pos, quitus.date_validite.strftime('%d/%m/%Y'))
    
    # ==================== SECTION INFORMATIONS ====================
    y_pos -= 15*mm
    
    # Texte du Directeur Général (placé très près du rectangle)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30*mm, y_pos, "Le Directeur Général du PORT AUTONOME DE LOME soussigné certifie que :")

    # Réduire l'espace entre le texte et le grand rectangle (petit espace de séparation)
    y_pos -= 3*mm

    # Grand rectangle unique pour toutes les informations (légèrement agrandi)
    hauteur_totale = 85*mm
    c.setLineWidth(1)
    # Conserver la coordonnée du sommet du rectangle pour les calculs suivants
    rect_top = y_pos
    c.rect(30*mm, rect_top - hauteur_totale, width - 60*mm, hauteur_totale, fill=0, stroke=1)
    
    # Section Client avec bande grise
    c.setFillColorRGB(*gris_clair)
    c.rect(30*mm, y_pos - 6*mm, width - 60*mm, 6*mm, fill=1, stroke=1)
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, y_pos - 4*mm, "LE CLIENT")
    
    # Informations du client
    y_pos -= 11*mm
    champs_client = [
        ("NOM ET PRENOMS", quitus.nom_prenoms),
        ("NOM / RAISON SOCIALE", quitus.raison_sociale or ""),
        ("N° CNI", quitus.cni),
        ("NATIONALITE", quitus.nationalite),
        ("ACTIVITE PRINCIPALE", quitus.activite),
        ("N° DE COMPTE PAL", quitus.compte_pal),
        ("N° D'IDENTIFICATION FISCALE", quitus.nif)
    ]
    
    c.setFont("Helvetica-Bold", 8)  # Police plus petite
    spacing_client = 5*mm  # Espacement réduit
    for label, valeur in champs_client:
        c.drawString(35*mm, y_pos, f"{label}:")
        c.setFont("Helvetica", 8)
        # Tronquer les textes trop longs
        if len(str(valeur)) > 40:  # Limite plus stricte
            valeur = str(valeur)[:37] + "..."
        c.drawString(95*mm, y_pos, str(valeur))
        c.setFont("Helvetica-Bold", 8)
        y_pos -= spacing_client
    
    # Section Adresse
    y_pos -= 2*mm
    c.setFillColorRGB(*gris_clair)
    c.rect(30*mm, y_pos - 6*mm, width - 60*mm, 6*mm, fill=1, stroke=1)
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, y_pos - 4*mm, "ADRESSE")
    
    # Informations d'adresse (augmenter la taille pour remplir tout l'encadré)
    y_pos -= 11*mm
    champs_adresse = [
        ("TELEPHONE MOBILE", quitus.telephone),
        ("E-MAIL", quitus.email),
        ("SITUATION GEOGRAPHIQUE", quitus.situation_geo),
        ("ADRESSE POSTALE", quitus.adresse_postale)
    ]

    # Labels plus visibles et valeurs plus grandes pour occuper l'espace
    c.setFont("Helvetica-Bold", 9)
    spacing_adresse = 6*mm  # Espacement augmenté pour meilleure lisibilité
    for label, valeur in champs_adresse:
        c.drawString(35*mm, y_pos, f"{label}:")
        c.setFont("Helvetica", 9)
        # Tronquer plus loin si nécessaire
        if len(str(valeur)) > 80:
            valeur = str(valeur)[:77] + "..."
        c.drawString(95*mm, y_pos, str(valeur))
        c.setFont("Helvetica-Bold", 9)
        y_pos -= spacing_adresse
    
    # ==================== TEXTE DE CERTIFICATION ====================
    # Placer le texte de certification juste sous le rectangle (petit espacement)
    cert_y = rect_top - hauteur_totale - 6*mm
    c.setFont("Helvetica", 9)  # Police plus petite
    date_presentation = datetime.now().strftime('%d/%m/%Y')
    texte1 = f"Présenté à la date du {date_presentation}"
    c.drawString(30*mm, cert_y, texte1)

    cert_y -= 6*mm  # Espacement réduit
    texte2 = "Une situation régulière avec le PORT AUTONOME DE LOME au regard des redevances"
    c.drawString(30*mm, cert_y, texte2)

    cert_y -= 4*mm
    texte3 = "portuaires dont il est redevable."
    c.drawString(30*mm, cert_y, texte3)

    cert_y -= 6*mm
    texte4 = "La présente attestation est délivrée pour servir et valoir ce que de droit pour la période du"
    c.drawString(30*mm, cert_y, texte4)

    cert_y -= 4*mm
    annee = quitus.date_validite.year
    texte5 = f"1er janvier au 31 décembre {annee}."
    c.drawString(30*mm, cert_y, texte5)
    
    # ==================== DATE ET SIGNATURE ====================
    # Position de base pour la signature (alignée avec QR code et TUV)
    signature_y = 64 * mm
    c.setFont("Helvetica", 10)
    date_emission = quitus.date_emission.strftime('%d/%m/%Y')
    c.drawRightString(width - 20*mm, signature_y, f"Fait à Lomé, le {date_emission}")

    # Nom du signataire sous la date (écart augmenté pour laisser plus d'espace)
    c.setFont("Helvetica-Bold", 11)
    # Réduire l'espace entre la date et le nom du Directeur Général (6 mm)
    director_y = signature_y - 6*mm
    c.drawRightString(width - 20*mm, director_y, "LE DIRECTEUR GENERAL")

    # Cadre pour la signature sous le nom du Directeur Général
    # Positionner le cadre légèrement sous le nom
    box_top = director_y - 4*mm
    # Agrandir le cadre de signature (hauteur 16 mm demandé) et le décaler légèrement à droite
    box_height = 16 * mm
    # Décalage léger vers la droite : on réduit la marge gauche du box (shift +5mm)
    box_left = width - 75*mm
    box_width = 60 * mm
    box_bottom = box_top - box_height
    c.setLineWidth(1)
    c.rect(box_left, box_bottom, box_width, box_height, fill=0, stroke=1)

    # Label sous le cadre de signature
    label_y = box_bottom - 4*mm
    c.setFont("Helvetica", 8)
    c.drawCentredString(box_left + box_width/2, label_y, "Signature et cachet")
    
    # ==================== QR CODE & LOGO TUV COTE A COTE - MEME LIGNE ====================
    qr_data = (
        f"https://www.togoport.tg/verifier/{quitus.code_verification}\n"
        f"QUITUS: {quitus.numero_quitus}\n"
        f"NOM: {quitus.nom_prenoms}\n"
        f"VALIDE: {quitus.date_validite.strftime('%d/%m/%Y')}"
    )
    qr_buffer = generer_qr_code(qr_data)
    qr_image = ImageReader(qr_buffer)

    # QR Code à gauche
    qr_size = 28*mm
    qr_x = 20*mm
    # Aligner QR code et signature sur la même ligne (même y que le bas du cadre signature)
    qr_y = box_bottom

    # TUV légèrement vers la gauche et vers le bas par rapport au QR code
    tuv_size = 45*mm
    # Déplacer légèrement vers la gauche (de 42% à 35%)
    tuv_x = width * 0.35  # Position plus à gauche
    # Descendre de 7mm par rapport au QR code
    tuv_y = qr_y - 9*mm  # 7mm plus bas que le QR code
    
    try:
        tuv_image = ImageReader(TUV_LOGO_PATH)
        # Ajuster le logo TUV dans un carré en conservant ratio (letterbox)
        c.drawImage(tuv_image, tuv_x, tuv_y, width=tuv_size, height=tuv_size, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
    c.setFont("Helvetica", 7)
    c.drawString(qr_x + 2*mm, qr_y - 2*mm, f"Code: {quitus.code_verification}")
    
    # ==================== NOTE EN BAS ====================
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width/2, 12*mm, "SEUL L'ORIGINAL DE CE DOCUMENT FAIT FOI")  # Déplacé vers le bas (de 15mm à 12mm)
    
    # ==================== PIED DE PAGE COLORÉ ====================
    c.setFillColorRGB(*jaune)
    c.rect(0, 0, width, 10*mm, fill=1, stroke=0)

    # Petits cercles bleus à gauche et à droite dans la bande jaune
    c.setFillColorRGB(*bleu_marine)
    # Agrandir les cercles pour quasi-atteindre la hauteur de la bande jaune (diamètre ~9.5mm)
    circle_r = 4.75 * mm
    c.circle(15*mm, 5*mm, circle_r, fill=1, stroke=0)
    c.circle(width - 15*mm, 5*mm, circle_r, fill=1, stroke=0)

    c.setFillColorRGB(*bleu_marine)
    c.setFont("Helvetica", 7)
    info_contact = "01 BP: 1225 Lomé 01  Tél: +228 22 27 47 42  Fax: +228 22 27 26 27 / 22 27 02 48  Lomé - TOGO"
    c.drawCentredString(width/2, 6*mm, info_contact)
    c.drawCentredString(width/2, 3*mm, "Email: togoport@togoport.tg  Website : https://www.togoport.tg")
    
    c.save()
    buffer.seek(0)
    return buffer