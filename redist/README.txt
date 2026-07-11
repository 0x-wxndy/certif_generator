Redistribuables Windows — Générateur de certificats
====================================================

Ce dossier contient (après téléchargement) les installateurs nécessaires
sur un PC Windows 10/11 cible.

Contenu attendu
---------------
  python-3.12.10-amd64.exe                      Python 3.12 (BUILD uniquement)
  VC_redist.x64.exe                             Visual C++ Redistributable
  MicrosoftEdgeWebView2RuntimeInstallerX64.exe  WebView2 (recommandé)
  LibreOffice_*_Win_x86-64.msi                  LibreOffice (PDF / aperçu)

Comment remplir ce dossier
--------------------------
  Double-cliquez :  download_redist.bat
  (connexion Internet requise)

Installation sur le PC cible
----------------------------
  1. Double-cliquez :  install_redist.bat
  2. Suivez les assistants
  3. Python 3.12 n'est utile QUE pour reconstruire l'EXE

Livraison
---------
  - dist\GenerateurCertificats\   (l'application)
  - redist\                       (installateurs)
  - Sur le PC cible: install_redist.bat une fois
  - Puis GenerateurCertificats.exe

  L'interface s'ouvre dans le NAVIGATEUR par défaut (mode fiable).
  Une boîte de dialogue reste ouverte : OK = fermer l'app.

  Après copie/ZIP: rien à faire — l'EXE débloque les DLL tout seul
  au démarrage (plus besoin de debloquer_dll.bat).

Conversion PDF
--------------
  Word s'il est installé (plus rapide), sinon LibreOffice.

Fenêtre native (optionnel)
--------------------------
  Créez le fichier fenetre_native.on à côté de l'EXE
  (nécessite WebView2). Sinon gardez le mode navigateur.
