# 🚀 Guide de Déploiement Fly.io - Backend

## ✅ Configuration Terminée

Votre backend est maintenant prêt pour Fly.io !

## 📋 Étapes sur Fly.io

### 1. Configuration sur le site Fly.io
```
App name: smart-school-backend
Organization: Personal
Current Working Directory: backend  ⚠️ IMPORTANT
Config path: fly.toml (par défaut)
```

### 2. Cliquez "Deploy" et attendez...

### 3. Après déploiement, configurez les variables d'environnement
Dans le dashboard Fly.io → Settings → Environment Variables :

```bash
FLASK_ENV = production
JWT_SECRET_KEY = your-super-secret-jwt-key-change-this-in-production
MONGODB_URI = mongodb+srv://username:password@cluster.mongodb.net/alexander_academy
PORT = 8080
```

## 🗄️ Base de Données MongoDB

### Option 1: MongoDB Atlas (Recommandé)
1. Allez sur [mongodb.com/atlas](https://mongodb.com/atlas)
2. Créez un cluster gratuit (M0)
3. Créez un utilisateur avec mot de passe
4. Ajoutez `0.0.0.0/0` aux IP autorisées
5. Copiez la connection string
6. Mettez à jour `MONGODB_URI` dans Fly.io

### Option 2: Fly.io MongoDB (Alternative)
```bash
flyctl postgres create --name smart-school-db
```

## 🔧 Fichiers Créés

1. **`backend/fly.toml`** - Configuration Fly.io
2. **`backend/Procfile`** - Commande de démarrage
3. **`backend/.env.production`** - Variables d'environnement
4. **Route `/api/health`** - Health check pour Fly.io
5. **CORS mis à jour** - Pour accepter Vercel

## 🌐 URLs Finales

- **Backend**: `https://smart-school-backend.fly.dev`
- **Health Check**: `https://smart-school-backend.fly.dev/api/health`
- **API Docs**: `https://smart-school-backend.fly.dev/api/docs`

## 🔄 Mettre à jour Vercel

Après déploiement du backend, mettez à jour dans Vercel :

```
REACT_APP_API_URL = https://smart-school-backend.fly.dev/api
```

## 🐛 Dépannage

### Build Failed
- Vérifiez que "Current Working Directory" = `backend`
- Vérifiez `requirements.txt` et `fly.toml`

### Connection Failed
- Vérifiez `MONGODB_URI` dans les variables d'environnement
- Testez la connection MongoDB manuellement

### CORS Errors
- Les origins Vercel sont déjà configurés dans le code

## ✅ Checklist Déploiement

- [ ] App créée sur Fly.io avec `backend` comme working directory
- [ ] Variables d'environnement configurées
- [ ] MongoDB Atlas configuré
- [ ] Backend déployé avec succès
- [ ] Health check fonctionne : `/api/health`
- [ ] REACT_APP_API_URL mis à jour dans Vercel
- [ ] Test complet frontend ↔ backend

**Votre backend sera accessible à `https://smart-school-backend.fly.dev` ! 🎯**