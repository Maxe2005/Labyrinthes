# Créé le 12/06/22
# Dernière modification : 24/10/22
# Auteur : Maxence CHOISEL

import csv
import tkinter as tk
from tkinter.simpledialog import askinteger
from math import*
from time import*


def init_fenetre (t_fen) :
    """
    Défini la fenêtre de travail
    :param t_fen: (str) la taille de la fenêtre à créer
    """
    fen = tk.Tk()
    fen.title ("Créer un labirinthe")
    fen.geometry (t_fen)
    return fen

def init_canvas (fen, x,y, color) :
    """
    Initialise le canvas de travail dans la fenêtre fen
    :param x: (int) la largueur du canvas à créer
    :param y: (int) la longueur du canvas à créer
    :param color: (int) la couleur du canvas à créer
    """
    canvas = tk.Canvas(fen, width= str(x), height= str(y), background= color)
    canvas.grid(column= 0, row= 0, columnspan= 9 )
    return canvas


def taille_auto () :
    """
    Calcule la taille en pixel d´un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition
    """
    global x_grille, y_grille, x_canvas, y_canvas
    if y_canvas / y_grille < x_canvas / x_grille :
        taille = y_canvas / (y_grille)
    else :
        taille = x_canvas / (x_grille)
    return round(taille)


def origines (taille) :
    """
    Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)
    :param taille: (int) la taille en pixels d´une case
    """
    global x_canvas, y_canvas, x_grille, y_grille
    origine_x = (x_canvas - (taille * (x_grille-1))) / 2
    origine_y = (y_canvas - (taille * (y_grille-1))) / 2
    assert origine_x > 0 and origine_y > 0
    return origine_x, origine_y


def trace_grille () :
    """
    Trace avec Tkinter un quadrillage de la grille g
    :param g: (list) la grille à tracer
    :param t: (int) la taille en pixels d´une case
    :param ox: (int) la position en abcsisses de l´origine du quadrillage sur le canvas
    :param oy: (int) la position en ordonnés de l´origine du quadrillage sur le canvas
    :param color_grille: (str) la couleur des traits du quadrillage
    :param color_canvas: (str) la couleur du font du quadrillage (donc le canvas)
    """
    global lab, ox, oy, t, color_canvas, color_grille
    for y in range (len(lab)) :
        for x in range (len(lab[y])) :
            if lab[y][x] == "1" or lab[y][x] == "3" :
                barre_horizontale (ox + x*t, oy + y*t, t, color_grille)
            if lab[y][x] == "2" or lab[y][x] == "3" :
                barre_verticale (ox + x*t, oy + y*t, t, color_grille)
    return


def barre_verticale (ox, oy, t, color) :
    """
    Trace dans le canvas une ligne verticale
    :param ox: (int) la position en pixel en abcsisse du début de la ligne
    :param oy: (int) la position en pixel en ordonnées du début de la ligne
    :param t: (int) la taille en pixel de la ligne
    :param color: (str) la couleur de la ligne
    """
    global canvas
    ligne = canvas.create_line (ox,oy,ox,oy+t, fill= color)
    return


def barre_horizontale (ox, oy, t, color) :
    """
    Trace dans le canvas une ligne verticale
    :param ox: (int) la position en pixel en abcsisse du début de la ligne
    :param oy: (int) la position en pixel en ordonnées du début de la ligne
    :param t: (int) la taille en pixel de la ligne
    :param color: (str) la couleur de la ligne
    """
    global canvas
    ligne = canvas.create_line (ox,oy,ox+t,oy, fill= color)
    return


def grille_pleine (x,y) :
    """
    Crée une grille sans trous
    :param x: (int) le nombre de cases en largeur
    :param y: (int) le nombre de cases en hauteur
    """
    assert type(x) and type(y) == int
    assert x > 0 and y > 0
    g = []
    """
    for j in range (y) :
        a = []
        for i in range (x) :
            a.append("3")
        a.append("2")
        g.append(a)
    a = []
    for i in range (x) :
        a.append("1")
    a.append("0")
    g.append(a)
    """
    for i in range (y) :
        g.append(["3"]*x+["2"])
    g.append(["1"]*x+["0"])
    return g


def inser_grille () :
    """
    Permet d´entrer une grille de labirinte (codé en 0,1,2,3) depuis la console
    """
    g = []
    count = 1
    while count != "fin" :
        a = input("Inserez la ligne n°"+str(count)+" de votre labirinthe ")
        if a != "fin" :
            if count == 1 :
                t = len(a)
            if len(a) == t :
                g.append(a)
                count += 1
            else :
                print ("Il y a une erreur dans la longueur de votre ligne, elle n´a pas la même longueur que la précédente !")
        else :
            count = "fin"
    return g


def save_as (numéro_du_lab, croquis, lab, entrée, sortie) :
    #print(lab)
    if croquis == True :
        nom = "Labyrinthes croquis\Croquis "+numéro_du_lab
    else :
        nom = "Labyrinthes classiques\Labyrinthe "+numéro_du_lab
    with open (nom, "w", newline = "") as f :
        for i in range (-2,len(lab)) :
            writer = csv.writer (f, delimiter = ",", lineterminator = "\n")
            if i == -2 :
                writer.writerow (entrée)
            elif i == -1 :
                writer.writerow (sortie)
            else :
                writer.writerow (lab[i])
    return


def move (x,y) :
    """
    Déplace la balle et toutes les autres choses à faire en même temps (pour ne pas avoir à les répéter dans haut, bas, gauche et droite)
    """
    global canvas, balle, t, x_balle, y_balle, nb_lab
    canvas.move(balle, x*t, y*t)
    y_balle += y
    x_balle += x
    texte.set("Labirinthe"+" "*10+str(x_balle)+" "+str(y_balle))
    return


def haut (event) :
    global lab, Sortie, Modif
    if y_balle > 0 and 0 <= x_balle <= x_grille-2 or Sortie == 1 :
        if Modif :
            if lab[y_balle][x_balle] == "2" :
                lab[y_balle][x_balle] = "3"
            elif lab[y_balle][x_balle] == "0" :
                lab[y_balle][x_balle] = "1"
            else :
                MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
            Modif = False
            texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
            refresh_lab ()
        else :
            if dep == 0 :
                if lab[y_balle][x_balle] == "3" :
                    lab[y_balle][x_balle] = "2"
                elif lab[y_balle][x_balle] == "1" :
                    lab[y_balle][x_balle] = "0"
                refresh_lab ()
            move(0,-1)
            if Sortie == 1 :
                sortie2 ()
    elif type(Sortie) == tuple :
        if y_balle-1 == Sortie[1] and x_balle == Sortie[0] :
            MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
            if MsgBox == 'yes':
                if lab[y_balle][x_balle] == "2" :
                    lab[y_balle][x_balle] = "3"
                elif lab[y_balle][x_balle] == "0" :
                    lab[y_balle][x_balle] = "1"
                refresh_lab ()
                Sortie = 0
                sortie_aff.set("Sortie")
    return

def bas (event) :
    global lab, Sortie, Modif
    if y_balle < y_grille-2 and 0 <= x_balle <= x_grille-2 or Sortie == 1 :
        if Modif :
            if lab[y_balle+1][x_balle] == "2" :
                lab[y_balle+1][x_balle] = "3"
            elif lab[y_balle+1][x_balle] == "0" :
                lab[y_balle+1][x_balle] = "1"
            else :
                MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
            Modif = False
            texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
            refresh_lab ()
        else :
            if dep == 0 :
                if lab[y_balle+1][x_balle] == "3" :
                    lab[y_balle+1][x_balle] = "2"
                elif lab[y_balle+1][x_balle] == "1" :
                    lab[y_balle+1][x_balle] = "0"
                refresh_lab ()
            move(0,1)
            if Sortie == 1 :
                sortie2 ()
    elif type(Sortie) == tuple :
        if y_balle+1 == Sortie[1] and x_balle == Sortie[0]:
            MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
            if MsgBox == 'yes':
                lab[y_balle+1][x_balle] = "1"
                refresh_lab ()
                Sortie = 0
                sortie_aff.set("Sortie")
    return

def droite (event) :
    global lab, Sortie, Modif
    if x_balle < x_grille-2 and 0 <= y_balle <= y_grille-2 or Sortie == 1 :
        if Modif :
            if lab[y_balle][x_balle+1] == "1" :
                lab[y_balle][x_balle+1] = "3"
            elif lab[y_balle][x_balle+1] == "0" :
                lab[y_balle][x_balle+1] = "2"
            else :
                MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
            Modif = False
            texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
            refresh_lab ()
        else :
            if dep == 0 :
                if lab[y_balle][x_balle+1] == "3" :
                    lab[y_balle][x_balle+1] = "1"
                elif lab[y_balle][x_balle+1] == "2" :
                    lab[y_balle][x_balle+1] = "0"
                refresh_lab ()
            move(1,0)
            if Sortie == 1 :
                sortie2 ()
    elif type(Sortie) == tuple :
        if x_balle+1 == Sortie[0] and y_balle == Sortie[1] :
            MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
            if MsgBox == 'yes':
                lab[y_balle][x_balle+1] = "2"
                refresh_lab ()
                Sortie = 0
                sortie_aff.set("Sortie")
    return

def gauche (event) :
    global lab, Sortie, Modif
    if x_balle > 0 and 0 <= y_balle <= y_grille-2 or Sortie == 1 :
        if Modif :
            if lab[y_balle][x_balle] == "1" :
                lab[y_balle][x_balle] = "3"
            elif lab[y_balle][x_balle] == "0" :
                lab[y_balle][x_balle] = "2"
            else :
                MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
            Modif = False
            texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
            refresh_lab ()
        else :
            if dep == 0 :
                if lab[y_balle][x_balle] == "3" :
                    lab[y_balle][x_balle] = "1"
                elif lab[y_balle][x_balle] == "2" :
                    lab[y_balle][x_balle] = "0"
                refresh_lab ()
            move(-1,0)
            if Sortie == 1 :
                sortie2 ()
    elif type(Sortie) == tuple :
        if x_balle-1 == Sortie[0] and y_balle == Sortie[1] :
            MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
            if MsgBox == 'yes':
                if lab[y_balle][x_balle] == "1" :
                    lab[y_balle][x_balle] = "3"
                elif lab[y_balle][x_balle] == "0" :
                    lab[y_balle][x_balle] = "2"
                refresh_lab ()
                Sortie = 0
                sortie_aff.set("Sortie")
    return


def aller_a () :
    """
    Permet d'aller directement au labirinthe de son choix
    """
    global x_balle, y_balle
    n = tk.simpledialog.askstring ( title = "Aller directement à" , prompt = "Nouvelle position de la balle :" , initialvalue = "x,y")
    if n is not(None):
        n = n.split(",")
        x = int(n[0])
        y = int(n[1])
        if 0 <= x < x_grille and 0 <= y < y_grille :
            canvas.move(balle, (x-x_balle)*t, (y-y_balle)*t)
            x_balle = x
            y_balle = y
            texte.set("Labirinthe"+" "*10+str(x_balle)+" "+str(y_balle))
        else :
            tk.messagebox.showinfo ('Aller directement à',"Cette position n'existe pas ! (Syntaxe : 'position_x,position_y')\navec 0 <= position_x <= "++", et ",icon = 'error')
    return


def init_balle () :
    global balle, x_balle, y_balle, ox, oy, t
    bordure = 1/10 *t
    o_x = round(ox + bordure)
    o_y = round(oy + bordure)
    pos_x = o_x + x_balle*t
    pos_y = o_y + y_balle*t
    t_balle = round(t-2*bordure)
    balle = canvas.create_oval (pos_x, pos_y, pos_x+t_balle, pos_y+t_balle,  fill= "blue", outline= "black")
    return


def init_lab (x,y) :
    """
    Initialise le labirinthe à afficher
    """
    global lab, x_grille, y_grille, x_balle, y_balle
    lab = grille_pleine (x,y)
    x_grille = x + 1
    y_grille = y + 1
    x_balle = 0
    y_balle = 0
    return


def sauvegarder () :
    n = tk.messagebox.askyesno ('Sauvegarder','Voulez-vous sauvegarder votre labirinthe comme un croquis (Yes : incomplet donc possibilité de le modifier plus tard) ou comme un labirinthe terminé (No : pas de possibilité de le modifier plus tard) ?')
    if n == True :
        e = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre croquis de labirinthe" , initialvalue = "")
        save_as (e, True, lab, Entrée, Sortie)
    elif n == False :
        if Entrée == 0 or Sortie == 0 :
            if Entrée == 0 and type(Sortie) == tuple :
                MsgBox = tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée valide !', icon= "error")
            elif Sortie == 0 and type(Entrée) == tuple :
                MsgBox = tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une sortie valide !', icon= "error")
            else :
                MsgBox = tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée et une sortie valide !', icon= "error")
        else :
            n = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre labirinthe" , initialvalue = "")
            save_as (n, False, lab, Entrée, Sortie)
    return


def nouveau_lab () :
    global lab, x_grille, y_grille, x_balle, y_balle, dep, deplace
    n = tk.messagebox.askyesno ('Nouveau labirinthe','Voulez-vous ouvrir un croquis déjà existant (Yes) ou voulez-vous créer un nouveau labirinthe (No) ?')
    if n == True :
        a = False
        while not(a) :
            n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nom du croquis que vous voulez récupérer (ce qui est écrit après 'Croquis ') :" , initialvalue = "")
            if n == None :
                a = True
            else :
                a = ouvrir_lab(n)
                if a == "fichier introuvable" :
                    a = False
                    tk.messagebox.showinfo ('Croqui introuvable','Le Croqui nommé : '+n+' est introuvable !',icon="error")
                else :
                    lab = a
                    x_grille = len(lab[0])
                    y_grille = len(lab)
                    x_balle = Entrée[0]
                    y_balle = Entrée[1]
                    programme()
                    deplace.set("Déplacement")
                    dep = 1
    elif n == False :
        n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nombre de cases en largeur et en hauteur de votre labirinthe :" , initialvalue = "largeur,hauteur")
        if n != None :
            n = n.split(",")
            x = int(n[0])
            y = int(n[1])
            if 2 < x < 51 and 2 < y < 36 :
                init_lab(x,y)
                programme()
            else :
                MsgBox = tk.messagebox.showinfo ('Nouveau labirinthe','Ce labirinthe n´a pas de dimentions valides : x(min:3, max:50) et y(min:3, max:35) !', icon= "error")
    return


def ouvrir_lab (nom_du_lab) :
    global Entrée, Sortie
    nom = "Labyrinthes croquis/Croquis "+nom_du_lab
    try :
        fichier = open (nom, "r")
    except :
        return "fichier introuvable"
    else :
        table = []
        count = 1
        for ligne in fichier :
            ligne = ligne.rstrip()
            tab = ligne.split(",")
            if count != 3 :
                for i in range (len(tab)) :
                    tab[i] = int(tab[i])
                if count == 1 :
                    Entrée = tab
                    entrer_aff.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
                    count += 1
                elif count == 2 :
                    Sortie = tab
                    sortie_aff.set("Sortie : {};{}".format(Sortie[0],Sortie[1]))
                    count += 1
            else :
                table.append(tab)
        fichier.close()
        return table


def Quitter () :
    global fen
    MsgBox = tk.messagebox.askquestion ('Quitter','Voulez-vous vraiment quitter le jeu?',icon = 'error')
    if MsgBox == 'yes':
        fen.destroy()
    return


def sortie () :
    global Sortie, dep
    if Modif :
        MsgBox = tk.messagebox.showinfo ('Instaler une sortie','Impossible car déjà en cours de création d´un mur !',icon = 'error')
    else :
        if type(Sortie) == tuple :
            MsgBox = tk.messagebox.showinfo ('Instaler une sortie','La sortie à déjà été définie !',icon = 'error')
        else :
            if x_balle == 0 or x_balle == x_grille-2 or y_balle == 0 or y_balle == y_grille-2 :
                Sortie = 1
                dep = 0
                MsgBox = tk.messagebox.showinfo ('Instaler une sortie','Vous pouvez créer votre sortie avec les flèches !')
                texte.set("Vous pouver créer la sortie avec les flèches")
            else :
                MsgBox = tk.messagebox.showinfo ('Instaler une sortie','Pour instaler une sortie vous devez psitionner la balle à l´endroit ou sera crée la sortie c´est à dire près d´un bord !',icon = 'error')
    return

def sortie2 () :
    global Sortie
    Sortie = (x_balle, y_balle)
    sortie_aff.set("Sortie : {};{}".format(Sortie[0],Sortie[1]))
    texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
    Depl ()
    return


def entrée () :
    global Entrée
    if Entrée == 0 :
        Entrée = (x_balle, y_balle)
        entrer_aff.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
    else :
        MsgBox = tk.messagebox.askquestion ('Nouvelle entrée','Voulez-vous vraiment redefinir l´entrée de votre labirinthe qui est à {};{} par {};{} ?'.format(Entrée[0],Entrée[1],x_balle,y_balle))
        if MsgBox == 'yes':
            Entrée = (x_balle, y_balle)
            entrer_aff.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
    return


def Depl () :
    Deplacement (None)
    return

def Deplacement (event) :
    global deplace, dep
    if dep == 0 :
        deplace.set("Déplacement")
        dep = 1
    else :
        deplace.set("Créer")
        dep = 0
    return


def init_boutons () :
    """
    Initalise et affiche dans la fenêtre fen les boutons quitter, suivant, recommencer et precedent
    """
    global deplace, dep, fen

    button_modif = tk.Button (fen, text='Modif', command=Modifiant)
    button_modif.grid(column= 0, row= 2, sticky=tk.EW)

    button_sauvegarder = tk.Button (fen, text='Sauvgarder', command=sauvegarder)
    button_sauvegarder.grid(column= 2, row= 2, sticky=tk.EW)

    button_creer = tk.Button (fen, text='Nouveau Labirinthe', command=nouveau_lab)
    button_creer.grid(column= 3, row= 2, sticky=tk.EW)

    button_sortie = tk.Button (fen, text='Créer une sortie', command=sortie)
    button_sortie.grid(column= 8, row= 2,sticky=tk.EW)

    button_entrer = tk.Button (fen, text='Créer une entrée', command=entrée)
    button_entrer.grid(column= 7, row= 2, sticky=tk.EW)

    deplace = tk.StringVar()
    deplace.set("Créer")
    dep = 0
    button_deplacement = tk.Button (fen, textvariable= deplace, command=Depl)
    button_deplacement.grid(column= 5, row= 2, sticky=tk.EW)

    button_aller_a = tk.Button (fen, text='Aller à', command=aller_a)
    button_aller_a.grid(column= 4, row= 2)
    return


def Modifiant () :
    global Modif
    if Sortie == 1 :
        tk.messagebox.showinfo ('Créer un mur',"Impossible car déjà en cours de création d'une sortie !",icon = 'error')
    else :
        Modif =  True
        #MsgBox = tk.messagebox.showinfo ('Créer un mur','Vous pouvez restaurer un mur avec les flèches')
        texte.set("Vous pouver créer un mur avec les flèches")
    return

def Modification (event) :
    global Modif
    if Modif :
        Modif = False
    else :
        Modifiant ()
    return


def refresh_lab () :
    global canvas
    canvas.delete("all")
    init_balle()
    trace_grille ()
    return


def programme () :
    global fen, lab, ox, oy, t, color_canvas, color_grille, nb_lab
    t = taille_auto ()
    (ox, oy) = origines (t)
    texte.set("Labirinthe "+" "*10+str(x_balle)+" "+str(y_balle))
    refresh_lab ()

    return

# Début du programme

Modif = False

init_lab(10,10) # Labirinthe par défaut

Entrée = 0
Sortie = 0

x_canvas = 900
y_canvas = 600

x_fen = x_canvas
y_fen = y_canvas + 60
color_canvas = "white"
color_grille = "black"

fen = init_fenetre(str(x_fen)+"x"+str(y_fen))
canvas = init_canvas(fen, x_canvas, y_canvas, color_canvas)

texte = tk.StringVar()
texte.set("Début")
nb_coups = tk.Label(fen, textvariable= texte)
nb_coups.grid(column= 4, row= 1)

sortie_aff = tk.StringVar()
sortie_aff.set("Sortie")
sortie_label = tk.Label(fen, textvariable= sortie_aff)
sortie_label.grid(column= 8, row= 1)

entrer_aff = tk.StringVar()
entrer_aff.set("Entrée")
entrer_label = tk.Label(fen, textvariable= entrer_aff)
entrer_label.grid(column= 7, row= 1)

init_boutons ()

up = fen.bind("<KeyRelease-Up>", haut)
down = fen.bind("<KeyRelease-Down>", bas)
right = fen.bind("<KeyRelease-Right>", droite)
left = fen.bind("<KeyRelease-Left>", gauche)
space = fen.bind("<space>", Deplacement)
m = fen.bind("<KeyRelease-m>", Modification)

programme()
fen.mainloop()





