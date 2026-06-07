CREATE DATABASE IF NOT EXISTS IFRI_MentorLink;
USE IFRI_MentorLink;

CREATE TABLE Utilisateurs (
    id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50),
    prenom VARCHAR(50),
    telephone VARCHAR(15) UNIQUE,
    email VARCHAR(100) UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    photo VARCHAR(255) NULL,
    filiere VARCHAR(50),
    niveau VARCHAR(25),
    Bio TEXT NULL
);

CREATE TABLE Matieres (
    id_matiere INT AUTO_INCREMENT PRIMARY KEY,
    nom_matiere VARCHAR(100)
);

CREATE TABLE Annonces (
    id_annonce INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT,
    type_annonce ENUM('offre','demande'),
    format_session ENUM('presentiel','en_ligne','les_deux') NOT NULL,
    description_perso TEXT,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut ENUM('actif','fermee') DEFAULT 'actif',
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur)
);

CREATE TABLE Disponibilites (
    id_dispo INT AUTO_INCREMENT PRIMARY KEY,
    jour ENUM('Lun','Mar','Mer','Jeu','Ven','Sam','Dim') NOT NULL,
    heure_debut TIME NOT NULL,
    heure_fin TIME NOT NULL
);

CREATE TABLE Discussions (
    id_discussion INT AUTO_INCREMENT PRIMARY KEY,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Messages (
    id_message INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT,
    id_discussion INT,
    contenu TEXT,
    date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
    lu BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_discussion) REFERENCES Discussions(id_discussion)
);

CREATE TABLE Reponses (
    id_reponse INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT,
    id_annonce INT,
    statut ENUM('en_attente','acceptee','refusee') DEFAULT 'en_attente',
    message_accomp TEXT NULL,
    date_reponse DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_annonce) REFERENCES Annonces(id_annonce),
    UNIQUE KEY (id_utilisateur, id_annonce)
);

CREATE TABLE Matching (
    id_matching INT AUTO_INCREMENT PRIMARY KEY,
    id_mentor INT NOT NULL,
    id_mentore INT NOT NULL,
    score_compatibilite FLOAT,
    date_matching DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut ENUM('propose','accepte','refuse') DEFAULT 'propose',
    FOREIGN KEY(id_mentor) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_mentore) REFERENCES Utilisateurs(id_utilisateur),
    UNIQUE KEY (id_mentor, id_mentore)
);

CREATE TABLE Notifications (
    id_notification INT AUTO_INCREMENT PRIMARY KEY,
    id_utilisateur INT,
    type_notif ENUM('message','match','reponse') NOT NULL,
    contenu TEXT,
    lu BOOLEAN DEFAULT FALSE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur)
);

-- Tables de liaison
CREATE TABLE MAITRISE (
    id_utilisateur INT,
    id_matiere INT,
    PRIMARY KEY(id_utilisateur, id_matiere),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
);

CREATE TABLE BESOIN (
    id_utilisateur INT,
    id_matiere INT,
    PRIMARY KEY(id_utilisateur, id_matiere),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
);

CREATE TABLE USER_DISPONIBILITE (
    id_utilisateur INT,
    id_dispo INT,
    PRIMARY KEY(id_utilisateur, id_dispo),
    FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_dispo) REFERENCES Disponibilites(id_dispo)
);

CREATE TABLE ANNONCE_MATIERE (
    id_annonce INT,
    id_matiere INT,
    PRIMARY KEY(id_annonce, id_matiere),
    FOREIGN KEY (id_annonce) REFERENCES Annonces(id_annonce),
    FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
);

CREATE TABLE ANNONCE_DISPONIBILITE (
    id_annonce INT,
    id_dispo INT,
    PRIMARY KEY(id_annonce, id_dispo),
    FOREIGN KEY (id_annonce) REFERENCES Annonces(id_annonce),
    FOREIGN KEY(id_dispo) REFERENCES Disponibilites(id_dispo)
);

CREATE TABLE PARTICIPATION (
    id_utilisateur INT,
    id_discussion INT,
    PRIMARY KEY(id_utilisateur, id_discussion),
    FOREIGN KEY(id_utilisateur) REFERENCES Utilisateurs(id_utilisateur),
    FOREIGN KEY(id_discussion) REFERENCES Discussions(id_discussion)
);

-- Donnees de test
INSERT INTO Utilisateurs (nom, prenom, telephone, email, mot_de_passe, filiere, niveau, bio)
VALUES
  ('Koffi', 'Aime', '97000001', 'aime.koffi@ifri.bj', 'hash_mdp_1', 'IA', 'L1', 'Passionne de Python et IA'),
  ('Mensah', 'Sarah', '97000002', 'sarah.mensah@ifri.bj', 'hash_mdp_2', 'GL', 'L1', 'Forte en algo'),
  ('Dossou', 'Marc', '97000003', 'marc.dossou@ifri.bj', 'hash_mdp_3', 'SI', 'L2', 'Specialiste BDD'),
  ('Agbessi', 'Fadel', '97000004', 'fadel.agbessi@ifri.bj', 'hash_mdp_4', 'IM', 'L1', 'Debutant en BDD'),
  ('Hounsou', 'Rita', '97000005', 'rita.hounsou@ifri.bj', 'hash_mdp_5', 'SE&IoT', 'L2', 'Bonne en reseaux'),
  ('Zannou', 'Paul', '97000006', 'paul.zannou@ifri.bj', 'hash_mdp_6', 'IA', 'L3', 'Mentor experimente');

INSERT INTO Matieres (nom_matiere) VALUES
  ('Algorithmique'), ('Python'), ('Bases de donnees'), ('Developpement web'),
  ('Algebre relationnelle'), ('Mathematiques'), ('Reseaux'), ('Linux');

INSERT INTO Disponibilites (jour, heure_debut, heure_fin) VALUES
  ('Lun', '08:00', '10:00'), ('Mar', '16:00', '18:00'),
  ('Mer', '14:00', '16:00'), ('Jeu', '13:00', '15:00'),
  ('Ven', '10:00', '12:00'), ('Sam', '09:00', '11:00');

-- MAITRISE
INSERT INTO MAITRISE (id_utilisateur, id_matiere) VALUES
  (1, 2), (1, 1), (2, 1), (3, 3), (3, 5), (5, 7), (6, 6), (6, 2), (6, 1);

-- BESOIN
INSERT INTO BESOIN (id_utilisateur, id_matiere) VALUES
  (1, 6), (2, 2), (2, 4), (4, 3), (4, 5), (5, 2);

-- Disponibilites utilisateurs
INSERT INTO USER_DISPONIBILITE (id_utilisateur, id_dispo) VALUES
  (1, 1), (1, 5), (2, 3), (2, 2), (3, 5), (3, 4), (4, 3), (5, 6), (6, 1), (6, 4);

-- Annonces
INSERT INTO Annonces (id_utilisateur, type_annonce, format_session, description_perso) VALUES
  (1, 'offre', 'en_ligne', 'Sessions Python pour debutants'),
  (2, 'demande', 'presentiel', 'Cherche mentor en Python'),
  (3, 'offre', 'les_deux', 'Soutien en Bases de donnees'),
  (5, 'demande', 'en_ligne', 'Aide urgente en Python');

INSERT INTO ANNONCE_MATIERE (id_annonce, id_matiere) VALUES
  (1, 2), (2, 2), (3, 3), (3, 5), (4, 2);

INSERT INTO ANNONCE_DISPONIBILITE (id_annonce, id_dispo) VALUES
  (1, 1), (1, 5), (2, 3), (3, 5), (3, 4), (4, 6);

-- Reponses
INSERT INTO Reponses (id_utilisateur, id_annonce, statut, message_accomp) VALUES
  (2, 1, 'en_attente', 'Interessee par vos sessions Python'),
  (4, 3, 'acceptee', 'Besoin d aide sur les jointures SQL');

-- Matching
INSERT INTO Matching (id_mentor, id_mentore, score_compatibilite, statut) VALUES
  (1, 2, 0.88, 'accepte'), (3, 4, 0.75, 'propose');

-- Discussions
INSERT INTO Discussions (date_creation) VALUES
  ('2026-06-02 10:00:00'), ('2026-06-03 15:00:00');

INSERT INTO PARTICIPATION (id_utilisateur, id_discussion) VALUES
  (1, 1), (2, 1), (3, 2), (4, 2);

INSERT INTO Messages (id_discussion, id_utilisateur, contenu, lu) VALUES
  (1, 2, 'Bonjour Aime, dispo lundi ?', FALSE),
  (1, 1, 'Oui lundi 8h parfait', TRUE),
  (2, 4, 'Bonsoir Marc, besoin d aide sur jointures', TRUE),
  (2, 3, 'Vendredi 10h on fait ca', FALSE);

-- Notifications
INSERT INTO Notifications (id_utilisateur, type_notif, contenu, lu) VALUES
  (1, 'reponse', 'Sarah a repondu a votre annonce', FALSE),
  (2, 'match', 'Nouveau matching avec Aime Koffi', FALSE),
  (3, 'message', 'Fadel vous a envoye un message', TRUE),
  (4, 'match', 'Nouveau matching avec Marc Dossou', FALSE);
