from db import *

print("Test rapide sur les fonctions du projet pour assuer la correspondance entre Flask et la BD\n")

print("1. Test get_user_by_email('aime.koffi@ifri.bj') :")
user = get_user_by_email("aime.koffi@ifri.bj")
print(user)
print()

print("2. Test get_user_by_id(1) :")
user2 = get_user_by_id(1)
print(user2)
print()

print("3. Test get_annonces() :")
annonces = get_annonces()
print(f"Nombre d'annonces actives : {len(annonces)}")
for a in annonces:
    print(f"   - {a['type_annonce']} par {a['prenom']} {a['nom']}")
print()

print("4. Test get_messages_by_discussion(1) :")
messages = get_messages_by_discussion(1)
print(f"Nombre de messages : {len(messages)}")
for m in messages:
    print(f"   - {m['prenom']} : {m['contenu'][:50]}...")
print()

print("5. Test get_notifications_non_lues(2) :")
notifs = get_notifications_non_lues(2)
print(f"Notifications non lues : {len(notifs)}")
for n in notifs:
    print(f"   - {n['type_notif']} : {n['contenu'][:50]}...")
print()

print("6. Test get_matches_for_user(1) :")
matches = get_matches_for_user(1)
print(f"Nombre de matchs : {len(matches)}")
for m in matches:
    print(f"   - Mentor: {m['mentor_prenom']} / Mentore: {m['mentore_prenom']} (score: {m['score_compatibilite']})")
print()

print("Tous les tests sont passés avec succès !")
