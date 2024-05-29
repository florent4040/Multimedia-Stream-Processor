import os
import subprocess
import json

def obtenir_streams(chemin_fichier):
    cmd = ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', chemin_fichier]
    resultat = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return json.loads(resultat.stdout)['streams']

def obtenir_langues_audio(streams):
    langues_audio = []
    for stream in streams:
        if stream['codec_type'] == 'audio' and 'tags' in stream:
            langue = stream['tags'].get('language', 'unknown')
            if langue not in langues_audio:
                langues_audio.append(langue)
    return langues_audio

def obtenir_sous_titres(streams):
    sous_titres = []
    for stream in streams:
        if stream['codec_type'] == 'subtitle':
            langue = stream['tags'].get('language', 'unknown')
            type_sous_titres = "Complets"
            if stream['disposition'].get('forced', 0) == 1 or 'forced' in stream.get('tags', {}).get('title', '').lower():
                type_sous_titres = "Forcés"
            sous_titres.append({'index': stream['index'], 'language': langue, 'type': type_sous_titres})
    return sous_titres

def afficher_options_langues_audio(langues_audio):
    for index, langue in enumerate(langues_audio, start=1):
        print(f"{index}. {langue}")
    print("")

def afficher_options_sous_titres(sous_titres):
    print("Sous-titres disponibles:")
    for index, sous_titre in enumerate(sous_titres, start=1):
        print(f"{index}. Langue: {sous_titre['language']}, Type: {sous_titre['type']}")
    print("0. Aucun sous-titre")
    print("")

def traiter_video(chemin_fichier_entree, chemin_fichier_sortie, langue_audio, sous_titres_indices):
    print(f"Traitement de {chemin_fichier_entree}...")
    streams = obtenir_streams(chemin_fichier_entree)

    cmd = ['ffmpeg', '-i', chemin_fichier_entree, '-map', '0:v']
    for stream in streams:
        if stream['codec_type'] == 'audio' and stream['tags'].get('language') == langue_audio:
            cmd.extend(['-map', f'0:{stream["index"]}'])
        elif stream['codec_type'] == 'subtitle' and stream['index'] in sous_titres_indices:
            cmd.extend(['-map', f'0:{stream["index"]}'])
    cmd.extend(['-c', 'copy', chemin_fichier_sortie])
    subprocess.run(cmd)
    return True

def verifier_changements(langues_audio_precedentes, sous_titres_precedents, langues_audio_actuelles, sous_titres_actuels):
    if langues_audio_precedentes != langues_audio_actuelles or sous_titres_precedents != sous_titres_actuels:
        return True
    return False

def traiter_videos(dossier):
    parametres_precedents = None

    for nom_fichier in os.listdir(dossier):
        if nom_fichier.endswith(('.mp4', '.mkv', '.avi')):
            chemin_fichier_entree = os.path.join(dossier, nom_fichier)
            chemin_fichier_sortie = os.path.join(dossier, 'traitement', nom_fichier)

            streams = obtenir_streams(chemin_fichier_entree)
            langues_audio = obtenir_langues_audio(streams)
            sous_titres = obtenir_sous_titres(streams)

            if parametres_precedents is None or verifier_changements(*parametres_precedents, langues_audio, sous_titres):
                print(f"Configuration des paramètres pour la vidéo {nom_fichier}:")
                afficher_options_langues_audio(langues_audio)
                audio_choix = int(input("Votre choix pour la piste audio (0 pour annuler) : "))
                if audio_choix == 0:
                    return False
                langue_audio = langues_audio[audio_choix - 1]

                afficher_options_sous_titres(sous_titres)
                sous_titres_choix = input("Choisissez le numéro des sous-titres à conserver (séparés par des virgules): ")
                sous_titres_indices = [sous_titres[int(index) - 1]['index'] for index in sous_titres_choix.split(',') if index.isdigit() and 0 < int(index) <= len(sous_titres)]

                parametres_precedents = (langues_audio, sous_titres)
                choix_precedents = (langue_audio, sous_titres_indices)
            else:
                langue_audio, sous_titres_indices = choix_precedents

            os.makedirs(os.path.dirname(chemin_fichier_sortie), exist_ok=True)
            traiter_video(chemin_fichier_entree, chemin_fichier_sortie, langue_audio, sous_titres_indices)

if __name__ == "__main__":
    dossier = os.path.dirname(os.path.abspath(__file__))
    traiter_videos(dossier)
