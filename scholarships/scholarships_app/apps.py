from django.apps import AppConfig

class ScholarshipsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scholarships_app' # Saxid: Waxaan ku daray xiritaankii ' (quote)

    def ready(self):
        # MUHIIM: Kani wuxuu isku xirayaa Signals-ka iyo Apps-ka
        # Si ogeysiisyada email-ka ay u shaqeeyaan marka status-ka la beddelo
        import scholarships_app.signals