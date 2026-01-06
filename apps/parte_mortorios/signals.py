from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ParteMortorio
from apps.content_management.models import CuñaPublicitaria

@receiver(post_save, sender=ParteMortorio)
def sincronizar_estado_cuña_desde_parte(sender, instance, created, **kwargs):
    """
    Sincroniza el estado de la cuña asociada cuando cambia el estado del parte mortorio.
    Mapping:
    - al_aire -> activa
    - pausado -> pausada
    - finalizado -> finalizada
    - pendiente -> pendiente_revision (o borrador/pausada?) -> Dejamos 'pausada' para que no salga al aire.
    """
    # Mapeo de estados Parte -> Cuña
    mapa_estados = {
        'al_aire': 'activa',
        'pausado': 'pausada',
        'finalizado': 'finalizada',
        'pendiente': 'pausada', # Si se marca pendiente, pausamos la cuña
    }
    
    nuevo_estado_cuna = mapa_estados.get(instance.estado)
    if not nuevo_estado_cuna:
        return

    # Buscar cuña asociada por tag
    # El tag es: "parte_mortorio,transmision_fallecimiento,{codigo}"
    try:
        # Usamos filter por si acaso hubiera duplicados (no debería)
        cuñas = CuñaPublicitaria.objects.filter(tags__contains=instance.codigo)
        for cuña in cuñas:
            if cuña.estado != nuevo_estado_cuna:
                print(f"🔄 Sincronizando Cuña {cuña.codigo} a estado {nuevo_estado_cuna} (por Parte {instance.codigo})")
                cuña.estado = nuevo_estado_cuna
                cuña.save()
    except Exception as e:
        print(f"❌ Error sincronizando cuña desde parte: {e}")

@receiver(post_save, sender=CuñaPublicitaria)
def sincronizar_estado_parte_desde_cuña(sender, instance, created, **kwargs):
    """
    Sincroniza el estado del parte mortorio cuando cambia el estado de la cuña.
    Mapping:
    - activa -> al_aire
    - pausada -> pausado
    - finalizada -> finalizado
    """
    # Verificar si es una cuña de parte mortorio
    if not instance.tags or 'parte_mortorio' not in instance.tags:
        return

    # Mapeo de estados Cuña -> Parte
    mapa_estados = {
        'activa': 'al_aire',
        'pausada': 'pausado',
        'finalizada': 'finalizado',
        # Si la cuña vuelve a borrador?
        'borrador': 'pendiente',
        'pendiente_revision': 'pendiente'
    }

    nuevo_estado_parte = mapa_estados.get(instance.estado)
    if not nuevo_estado_parte:
        return

    # Extraer código del parte desde los tags
    # Tags format: "parte_mortorio,transmision_fallecimiento,PM000001"
    program_cod = None
    try:
        tags = instance.tags.split(',')
        for tag in tags:
            tag = tag.strip()
            if tag.startswith('PM') and len(tag) > 2: # Asumiendo código PM...
                program_cod = tag
                break
        
        if program_cod:
            parte = ParteMortorio.objects.filter(codigo=program_cod).first()
            if parte and parte.estado != nuevo_estado_parte:
                print(f"🔄 Sincronizando Parte {parte.codigo} a estado {nuevo_estado_parte} (por Cuña {instance.codigo})")
                parte.estado = nuevo_estado_parte
                parte.save()
    except Exception as e:
        print(f"❌ Error sincronizando parte desde cuña: {e}")
