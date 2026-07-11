Redistribuables Windows — Générateur de certificats
====================================================

Ce dossier contient (après téléchargement) les installateurs nécessaires
sur un PC Windows 11 cible.

Contenu attendu
---------------
  python-3.12.10-amd64.exe     Python 3.12 (pour BUILD de l'EXE uniquement)
  VC_redist.x64.exe            Visual C++ Redistributable
  LibreOffice_*_Win_x86-64.msi LibreOffice (aperçu / conversion PDF)

Comment remplir ce dossier
--------------------------
  Double-cliquez :  download_redist.bat
  (connexion Internet requise, ~350 Mo)

Installation sur le PC cible
----------------------------
  1. Double-cliquez :  install_redist.bat
  2. Suivez les assistants (LibreOffice + VC++)
  3. Python 3.12 n'est utile QUE si vous reconstruisez l'EXE
     (pas nécessaire pour les utilisateurs finaux qui reçoivent dist\)

Livraison recommandée
---------------------
  - Dossier dist\GenerateurCertificats\   (l'application)
  - Dossier redist\                      (installateurs)
  - Dire à l'utilisateur de lancer install_redist.bat une fois,
    puis GenerateurCertificats.exe

Notes
-----
  - Les .exe / .msi ne sont pas versionnés dans Git (trop lourds).
  - Relancez download_redist.bat pour les récupérer.
