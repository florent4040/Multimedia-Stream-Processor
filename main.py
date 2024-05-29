import os
import subprocess
import json
from inquirer import prompt

def obtenir_streams(chemin_fichier):
    cmd = ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', chemin_fichier]
    resultat = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return json.loads(resultat.stdout)['streams']

def obtenir_audio_japonais(streams):
    for stream in streams:
        if stream['codec_type'] == 'audio' and 'tags' in stream and stream['tags'].get('language') == 'jpn':
            return stream['index']
    return None

def obtenir_sous_titres_complets_francais(streams):
    sous_titres_complets = []
    for stream in streams:
        if stream['codec_type'] == 'subtitle':
            language = stream['tags'].get('language', 'unknown')
            forced = stream['disposition'].get('forced', 0)
            if language == 'fre' and forced == 0:
                sous_titres_complets.append(stream)
    return sous_titres_complets

def afficher_options_audio(streams):
    options = []
    for stream in streams:
        if stream['codec_type'] == 'audio':
            options.append({'name': f"Stream {stream['index']} - {stream['tags'].get('language', 'unknown')}", 'value': stream['index']})
    return options

def afficher_options_sous_titres(streams):
    options = []
    for stream in streams:
        options.append({'name': f"Stream {stream['index']} - {stream['tags'].get('language', 'unknown')}", 'value': stream['index']})
    return options

def traiter_videos(dossier):
    dossier_sortie = os.path.join(dossier, 'traitement')
    if not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)

    for nom_fichier in os.listdir(dossier):
        if nom_fichier.endswith(('.mp4', '.mkv', '.avi')):  
            chemin_fichier_entree = os.path.join(dossier, nom_fichier)
            chemin_fichier_sortie = os.path.join(dossier_sortie, nom_fichier)

            streams = obtenir_streams(chemin_fichier_entree)
            audio_stream = obtenir_audio_japonais(streams)
            sous_titres_streams = obtenir_sous_titres_complets_francais(streams)

            if not audio_stream:
                print("Audio japonais non trouvé pour", nom_fichier)
                continue
            print("Audio japonais trouvé pour", nom_fichier)

            options_audio = afficher_options_audio(streams)
            options_sous_titres = afficher_options_sous_titres(sous_titres_streams)

            questions = [
                {
                    'type': 'list',
                    'name': 'audio',
                    'message': 'Choisissez l\'audio à conserver:',
                    'choices': options_audio
                },
                {
                    'type': 'checkbox',
                    'name': 'sous_titres',
                    'message': 'Choisissez les sous-titres à conserver (appuyez sur <space> pour sélectionner/désélectionner):',
                    'choices': options_sous_titres
                }
            ]

            reponses = prompt(questions)

            cmd = ['ffmpeg', '-i', chemin_fichier_entree, '-map', '0:v']  
            cmd.extend(['-map', f'0:{reponses["audio"]}'])  
            for stream in reponses["sous_titres"]:
                cmd.extend(['-map', f'0:{stream["index"]}'])
            cmd.extend(['-c', 'copy', chemin_fichier_sortie])
            subprocess.run(cmd)

if __name__ == "__main__":
    dossier = os.path.dirname(os.path.abspath(__file__))  
    traiter_videos(dossier)
