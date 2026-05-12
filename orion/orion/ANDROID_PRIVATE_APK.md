# APK privado do ORION Legacy Edition

O APK não guarda chave Groq. Ele abre o servidor Flask do Orion por WebView.

## Como funciona

1. O computador roda `python app.py`.
2. O Android entra no mesmo Wi-Fi.
3. O app Android abre `http://IP_DO_COMPUTADOR:5000`.

## Gerar APK

Instale:

- Android Studio
- JDK 17

Depois abra a pasta:

```txt
orion-android
```

No Android Studio:

```txt
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

## Importante

Para a IA funcionar, o servidor Flask precisa estar ligado. Isso mantém a chave segura fora do APK.
