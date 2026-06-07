DROP DATABASE IF EXISTS IFRI_MentorLink;
CREATE DATABASE IFRI_MentorLink;
USE IFRI_MentorLink;        
CREATE TABLE Utilisateurs
(
     id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
     nom VARCHAR(50),
     prenom varchar(50),
     telephone varchar(15)UNIQUE,
     email varchar(100)UNIQUE,
     mot_de_passe varchar(255)NOT NULL,
     photo varchar(255)NULL,
     filiere varchar(50),
     niveau varchar(25),
     Bio TEXT NULL
);

CREATE TABLE Matières
(
    id_matiere INT AUTO_INCREMENT PRIMARY KEY,
    nom_matiere VARCHAR(100)
);

CREATE TABLE Annonces
(
    id_annonce INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT, FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    type_annonce ENUM('offre','demande'),
    format_session ENUM('présentiel','en_ligne','les_deux') NOT NULL,
    description_perso TEXT,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut ENUM('actif','fermée') DEFAULT 'actif'
);

CREATE TABLE Disponibilités
(
    id_dispo INT AUTO_INCREMENT PRIMARY KEY,
    jour ENUM('Lun','Mar','Mer','Jeu','Ven','Sam','Dim') NOT NULL,
    heure_debut TIME NOT NULL,
    heure_fin TIME NOT NULL
);

CREATE TABLE Discussions
(
    id_discussion INT AUTO_INCREMENT PRIMARY KEY,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Messages
(
id_message INT AUTO_INCREMENT PRIMARY KEY,
id_utilisateur INT,FOREIGN KEY(id_utilisateur)REFERENCES Utilisateurs(id_utilisateur),
id_discussion INT,FOREIGN KEY(id_discussion) REFERENCES Discussions(id_discussion),
contenu TEXT,
date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
lu BOOLEAN DEFAULT FALSE
);

CREATE TABLE Réponses
(
id_reponse INT AUTO_INCREMENT PRIMARY KEY,
id_utilisateur INT,FOREIGN KEY(id_utilisateur)REFERENCES Utilisateurs(id_utilisateur),
id_annonce INT,FOREIGN KEY(id_annonce) REFERENCES Annonces(id_annonce),
statut ENUM('en_attente','acceptée','refusée') DEFAULT 'en_attente',
message_accomp TEXT NULL,
date_reponse DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Matching
(
    id_matching INT AUTO_INCREMENT PRIMARY KEY,
    id_mentor INT NOT NULL,
    id_mentore INT NOT NULL,
    score_compatibilite FLOAT,
    date_matching DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut ENUM('propose','accepte','refuse') DEFAULT 'propose',
    FOREIGN KEY(id_mentor)REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_mentore)REFERENCES Utilisateurs(id_utilisateur)
);

CREATE TABLE Notifications
(
    id_notification INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT,FOREIGN KEY(id_utilisateur)REFERENCES Utilisateurs(id_utilisateur),
    type_notif ENUM('message','match','réponse') NOT NULL,
    contenu TEXT,
    lu BOOLEAN DEFAULT FALSE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table de liaison-- 
CREATE TABLE IF NOT EXISTS MAITRISE
(
    id_utilisateur INT,
    id_matiere INT,
    PRIMARY KEY(id_utilisateur,id_matiere),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_matiere) REFERENCES Matières(id_matiere)
);

CREATE TABLE IF NOT EXISTS BESOIN
(
    id_utilisateur INT,
    id_matiere INT,
    PRIMARY KEY(id_utilisateur,id_matiere),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_matiere) REFERENCES Matières(id_matiere)
);

CREATE TABLE IF NOT EXISTS USER_DISPONIBILITE
(
    id_utilisateur INT,
    id_dispo INT,
    PRIMARY KEY(id_utilisateur,id_dispo),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_dispo) REFERENCES Disponibilités (id_dispo)
);

CREATE TABLE IF NOT EXISTS ANNONCE_MATIERE
(
    id_annonce INT,
    id_matiere INT,
    PRIMARY KEY(id_annonce,id_matiere),
    FOREIGN KEY (id_annonce) REFERENCES Annonces(id_annonce),
    FOREIGN KEY(id_matiere) REFERENCES Matières(id_matiere)
);

CREATE TABLE IF NOT EXISTS ANNONCE_DISPONIBILITE
(
id_annonce INT,
id_dispo INT,
PRIMARY KEY(id_annonce,id_dispo),
FOREIGN KEY (id_annonce) REFERENCES Annonces(id_annonce),
FOREIGN KEY(id_dispo) REFERENCES Disponibilités(id_dispo)
);

CREATE TABLE IF NOT EXISTS PARTICIPATION
(
    id_utilisateur INT,
    id_discussion INT,
    PRIMARY KEY(id_utilisateur,id_discussion),
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_discussion) REFERENCES Discussions(id_discussion)
);

-- Empêcher les doublons:éviter qu'un utilisateur réponde 2X à la mm annonce:un utilisateur ne peut répondre qu'une et une seul fois à la mm annonce.
ALTER TABLE `Réponses`
ADD UNIQUE (id_utilisateur, id_annonce);

-- Empêcher un doublon de paire mentor/mentoré:le couple mentor/mentoré ne peut avoir qu'un seul matching actif.
ALTER TABLE Matching
ADD UNIQUE (id_mentor, id_mentore);

-- ============================================================
-- DONNÉES DE TEST
-- Ordre important : sans FK d'abord, avec FK ensuite
-- ============================================================
 

-- 6 Utilisateurs (filières différentes)
-- Note : en production les mots de passe seront hashés avec bcrypt
INSERT INTO Utilisateurs (nom, prenom, telephone, email, mot_de_passe, filiere, niveau, bio)
VALUES
  ('Koffi',   'Aimé',   '97000001', 'aime.koffi@ifri.bj',   'hash_mdp_1', 'IA',     'L1', 'Passionné de Python et d''IA, je cherche à progresser en maths.'),
  ('Mensah',  'Sarah',  '97000002', 'sarah.mensah@ifri.bj',  'hash_mdp_2', 'GL',     'L1', 'Forte en algo, je veux améliorer mes bases en Python.'),
  ('Dossou',  'Marc',   '97000003', 'marc.dossou@ifri.bj',   'hash_mdp_3', 'SI',     'L2', 'Spécialiste BDD, disponible pour aider les L1.'),
  ('Agbessi', 'Fadel',  '97000004', 'fadel.agbessi@ifri.bj', 'hash_mdp_4', 'IM',     'L1', 'Débutant en BDD, motivé à apprendre.'),
  ('Hounsou', 'Rita',   '97000005', 'rita.hounsou@ifri.bj',  'hash_mdp_5', 'SE&IoT', 'L2', 'Bonne en réseaux, je cherche de l''aide en Python.'),
  ('Zannou',  'Paul',   '97000006', 'paul.zannou@ifri.bj',   'hash_mdp_6', 'IA',     'L3', 'Mentor expérimenté, maîtrise Python, Maths et Algo.');
 
-- 8 Matières
INSERT INTO Matières (nom_matiere)
VALUES
  ('Algorithmique'),
  ('Python'),
  ('Bases de donnees'),
  ('Developpement web'),
  ('Algebre relationnelle'),
  ('Mathematiques'),
  ('Reseaux'),
  ('Linux');
 
-- 6 Créneaux de disponibilité
INSERT INTO Disponibilités (jour, heure_debut, heure_fin)
VALUES
  ('Lun', '08:00', '10:00'),
  ('Mar', '16:00', '18:00'),
  ('Mer', '14:00', '16:00'),
  ('Jeu', '13:00', '15:00'),
  ('Ven', '10:00', '12:00'),
  ('Sam', '09:00', '11:00');
 
-- Points forts (MAITRISE)
-- Koffi : Python, Algo | Marc : BDD, Algèbre rel. | Rita : Réseaux | Paul : Maths, Python, Algo
INSERT INTO MAITRISE (id_utilisateur, id_matiere)
VALUES
  (1, 2), -- Koffi maîtrise Python
  (1, 1), -- Koffi maîtrise Algorithmique
  (2, 1), -- Sarah maîtrise Algorithmique
  (3, 3), -- Marc maîtrise Bases de données
  (3, 5), -- Marc maîtrise Algèbre relationnelle
  (5, 7), -- Rita maîtrise Réseaux
  (6, 6), -- Paul maîtrise Mathématiques
  (6, 2), -- Paul maîtrise Python
  (6, 1); -- Paul maîtrise Algorithmique
 
-- Points faibles (BESOIN)
INSERT INTO BESOIN (id_utilisateur, id_matiere)
VALUES
  (1, 6), -- Koffi a besoin de Mathématiques
  (2, 2), -- Sarah a besoin de Python
  (2, 4), -- Sarah a besoin de Dev web
  (4, 3), -- Fadel a besoin de Bases de données
  (4, 5), -- Fadel a besoin d'Algèbre relationnelle
  (5, 2); -- Rita a besoin de Python
 
-- Disponibilités des utilisateurs
INSERT INTO USER_DISPONIBILITE (id_utilisateur, id_dispo)
VALUES
  (1, 1), -- Koffi : Lundi 8h-10h
  (1, 5), -- Koffi : Vendredi 10h-12h
  (2, 3), -- Sarah : Mercredi 14h-16h
  (2, 2), -- Sarah : Mardi 16h-18h
  (3, 5), -- Marc : Vendredi 10h-12h
  (3, 4), -- Marc : Jeudi 13h-15h
  (4, 3), -- Fadel : Mercredi 14h-16h
  (5, 6), -- Rita : Samedi 9h-11h
  (6, 1), -- Paul : Lundi 8h-10h
  (6, 4); -- Paul : Jeudi 13h-15h
 
-- 4 Annonces
INSERT INTO Annonces (id_utilisateur, type_annonce, format_session, description_perso)
VALUES
  (1, 'offre',   'en_ligne',  'Je propose des sessions Python pour débutants, exercices pratiques.'),
  (2, 'demande', 'presentiel','Cherche mentor en Python, disponible en semaine.'),
  (3, 'offre',   'les_deux',  'J''offre du soutien en Bases de données et algèbre relationnelle, L1 bienvenus.'),
  (5, 'demande', 'en_ligne',  'Cherche de l''aide urgente en Python pour mes projets IoT.');
 
-- Liaison Annonces ↔ Matières
INSERT INTO ANNONCE_MATIERE (id_annonce, id_matiere)
VALUES
  (1, 2), -- Annonce 1 (offre Koffi) → Python
  (2, 2), -- Annonce 2 (demande Sarah) → Python
  (3, 3), -- Annonce 3 (offre Marc) → Bases de données
  (3, 5), -- Annonce 3 (offre Marc) → Algèbre relationnelle
  (4, 2); -- Annonce 4 (demande Rita) → Python
 
-- Liaison Annonces ↔ Disponibilités
INSERT INTO ANNONCE_DISPONIBILITE (id_annonce, id_dispo)
VALUES
  (1, 1), -- Annonce Koffi → Lundi 8h-10h
  (1, 5), -- Annonce Koffi → Vendredi 10h-12h
  (2, 3), -- Annonce Sarah → Mercredi 14h-16h
  (3, 5), -- Annonce Marc → Vendredi 10h-12h
  (3, 4), -- Annonce Marc → Jeudi 13h-15h
  (4, 6); -- Annonce Rita → Samedi 9h-11h
 
-- 2 Réponses à des annonces
INSERT INTO Réponses (id_utilisateur, id_annonce, statut, message_accomp)
VALUES
  (2, 1, 'en_attente', 'Bonjour Aimé, je suis très intéressée par tes sessions Python !'),
  (4, 3, 'acceptée',   'Merci Marc, j''ai besoin d''aide surtout sur les jointures SQL.');
 
-- 2 Matchings générés par l'algorithme
INSERT INTO Matching (id_mentor, id_mentore, score_compatibilite, statut)
VALUES
  (1, 2, 0.88, 'accepte'), -- Koffi mentor de Sarah
  (3, 4, 0.75, 'propose'); -- Marc proposé mentor de Fadel
 
-- 2 Discussions ouvertes
INSERT INTO Discussions (date_creation)
VALUES
  ('2026-06-02 10:00:00'), -- Discussion Koffi ↔ Sarah
  ('2026-06-03 15:00:00'); -- Discussion Marc ↔ Fadel
 
-- Participation aux discussions
INSERT INTO PARTICIPATION (id_utilisateur, id_discussion)
VALUES
  (1, 1), -- Koffi dans discussion 1
  (2, 1), -- Sarah dans discussion 1
  (3, 2), -- Marc dans discussion 2
  (4, 2); -- Fadel dans discussion 2
 
-- Messages dans les discussions
INSERT INTO Messages (id_discussion, id_utilisateur, contenu, lu)
VALUES
  (1, 2, 'Bonjour Aimé ! Tu es toujours dispo lundi matin pour une session Python ?', FALSE),
  (1, 1, 'Oui Sarah, lundi 8h c''est parfait. On commence par les fonctions ?',        TRUE),
  (1, 2, 'Super ! J''apporte mes exercices du cours.',                                  FALSE),
  (2, 4, 'Bonsoir Marc, j''ai du mal avec les jointures. Tu peux m''aider ?',           TRUE),
  (2, 3, 'Bien sûr Fadel, vendredi 10h on fait ça ensemble.',                           FALSE);
 
-- 4 Notifications
INSERT INTO Notifications (id_utilisateur, type_notif, contenu, lu)
VALUES
  (1, 'reponse', 'Sarah Mensah a répondu à votre annonce Python.',              FALSE),
  (2, 'match',   'Nouveau matching : Aimé Koffi correspond à votre recherche.', FALSE),
  (3, 'message', 'Fadel Agbessi vous a envoyé un message.',                     TRUE),
  (4, 'match',   'Nouveau matching : Marc Dossou est disponible pour vous.',    FALSE);
 