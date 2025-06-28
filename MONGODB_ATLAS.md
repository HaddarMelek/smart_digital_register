# 🍃 MongoDB Atlas Setup (Optionnel)

## Pourquoi MongoDB Atlas ?

Render ne fournit pas de base de données gratuite. Vos données actuelles sont stockées localement et seront perdues sur Render sans une vraie base de données.

## 🚀 Setup Rapide MongoDB Atlas (Gratuit)

### 1. Créer un Compte
- Allez sur [mongodb.com/atlas](https://www.mongodb.com/atlas)
- Cliquez **"Try Free"**
- Inscrivez-vous avec Google/GitHub

### 2. Créer un Cluster
- Sélectionnez **M0 Sandbox** (Gratuit - 512 MB)
- Région : **AWS / us-east-1** (plus proche de Render)
- Nom : `alexander-academy`

### 3. Créer un Utilisateur
- **Database Access** → **Add New Database User**
- Username : `admin`
- Password : `generer-mot-de-passe-fort`
- Rôle : `Atlas Admin`

### 4. Configurer l'Accès Réseau
- **Network Access** → **Add IP Address**
- Sélectionnez **"Allow Access from Anywhere"** (`0.0.0.0/0`)
- *(Nécessaire pour Render)*

### 5. Obtenir la Connection String
- **Clusters** → **Connect** → **Connect your application**
- Copiez l'URL : `mongodb+srv://admin:PASSWORD@alexander-academy.xxxxx.mongodb.net/alexander_academy`
- Remplacez `<password>` par votre vrai mot de passe

### 6. Ajouter sur Render
Dans les variables d'environnement Render :
```
MONGO_URI = mongodb+srv://admin:votre-password@alexander-academy.xxxxx.mongodb.net/alexander_academy
```

## 🎯 Alternative : Déploiement Sans Base de Données

Votre app peut fonctionner sans MongoDB Atlas :
- Les données seront temporaires (perdues au redémarrage)
- Parfait pour démo/test
- Pas de configuration supplémentaire nécessaire

## ✅ Recommandation

- **Pour test/démo** : Pas besoin de MongoDB Atlas
- **Pour production** : Utilisez MongoDB Atlas (gratuit 512 MB)

**MongoDB Atlas = Données persistantes 📊**