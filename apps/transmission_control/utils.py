"""
Funciones de utilidad para el módulo de Control de Transmisiones
Sistema PubliTrack - Utilidades y helpers para transmisiones
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count, Sum, Avg
from django.conf import settings

from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    LogTransmision,
    EventoSistema
)


# ==================== UTILIDADES DE TIEMPO ====================

def formatear_duracion(segundos: int) -> str:
    """
    Convierte segundos a formato mm:ss
    """
    if not segundos:
        return "00:00"
    
    minutos = segundos // 60
    segundos_restantes = segundos % 60
    return f"{minutos:02d}:{segundos_restantes:02d}"


def formatear_duracion_extendida(segundos: int) -> str:
    """
    Convierte segundos a formato hh:mm:ss
    """
    if not segundos:
        return "00:00:00"
    
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos_restantes = segundos % 60
    
    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"


def parsear_horario(horario_str: str) -> Optional[time]:
    """
    Convierte string HH:MM a objeto time
    """
    try:
        hora, minuto = map(int, horario_str.split(':'))
        return time(hora, minuto)
    except (ValueError, AttributeError):
        return None


def obtener_inicio_dia(fecha=None):
    """
    Obtiene el inicio del día (00:00:00)
    """
    if fecha is None:
        fecha = timezone.now().date()
    
    inicio = datetime.combine(fecha, time.min)
    return timezone.make_aware(inicio) if timezone.is_naive(inicio) else inicio


def obtener_fin_dia(fecha=None):
    """
    Obtiene el fin del día (23:59:59)
    """
    if fecha is None:
        fecha = timezone.now().date()
    
    fin = datetime.combine(fecha, time.max)
    return timezone.make_aware(fin) if timezone.is_naive(fin) else fin


def calcular_overlap(inicio1, fin1, inicio2, fin2):
    """
    Calcula si dos rangos de tiempo se solapan y por cuánto
    """
    if inicio1 >= fin2 or inicio2 >= fin1:
        return False, 0
    
    overlap_inicio = max(inicio1, inicio2)
    overlap_fin = min(fin1, fin2)
    overlap_duracion = (overlap_fin - overlap_inicio).total_seconds()
    
    return True, overlap_duracion


# ==================== UTILIDADES DE CONFIGURACIÓN ====================

def obtener_configuracion_cache():
    """
    Obtiene la configuración activa con cache
    """
    config = cache.get('configuracion_transmision_activa')
    if config is None:
        config = ConfiguracionTransmision.get_configuracion_activa()
        if config:
            cache.set('configuracion_transmision_activa', config, timeout=300)  # 5 minutos
    return config


def esta_en_horario_transmision(hora=None):
    """
    Verifica si está en horario de transmisión según configuración
    """
    config = obtener_configuracion_cache()
    if not config:
        return False
    
    return config.esta_en_horario_transmision(hora)


def calcular_proxima_ventana_transmision():
    """
    Calcula cuándo es la próxima ventana de transmisión
    """
    config = obtener_configuracion_cache()
    if not config:
        return None
    
    ahora = timezone.now()
    hora_actual = ahora.time()
    
    # Si estamos en horario, retornar ahora
    if config.esta_en_horario_transmision(hora_actual):
        return ahora
    
    # Calcular próxima ventana
    if hora_actual < config.hora_inicio_transmision:
        # Mismo día
        proxima = datetime.combine(ahora.date(), config.hora_inicio_transmision)
    else:
        # Día siguiente
        mañana = ahora.date() + timedelta(days=1)
        proxima = datetime.combine(mañana, config.hora_inicio_transmision)
    
    return timezone.make_aware(proxima) if timezone.is_naive(proxima) else proxima


# ==================== UTILIDADES DE PROGRAMACIÓN ====================

def validar_horarios_especificos(horarios: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida una lista de horarios específicos
    Retorna (es_valido, errores)
    """
    errores = []
    
    if not isinstance(horarios, list):
        return False, ["Los horarios deben ser una lista"]
    
    for i, horario in enumerate(horarios):
        if not isinstance(horario, str):
            errores.append(f"Horario {i+1}: debe ser string")
            continue
        
        try:
            datetime.strptime(horario, '%H:%M')
        except ValueError:
            errores.append(f"Horario {i+1}: formato inválido '{horario}' (use HH:MM)")
    
    # Verificar duplicados
    if len(horarios) != len(set(horarios)):
        errores.append("Hay horarios duplicados")
    
    return len(errores) == 0, errores


def calcular_distribución_automatica(repeticiones_por_dia: int, inicio: time, fin: time) -> List[str]:
    """
    Calcula distribución automática de horarios
    """
    if repeticiones_por_dia <= 0:
        return []
    
    # Convertir a minutos
    inicio_minutos = inicio.hour * 60 + inicio.minute
    fin_minutos = fin.hour * 60 + fin.minute
    
    # Calcular intervalo
    duracion_total = fin_minutos - inicio_minutos
    if duracion_total <= 0:
        return []
    
    intervalo = duracion_total / repeticiones_por_dia
    
    horarios = []
    for i in range(repeticiones_por_dia):
        minutos = inicio_minutos + (i * intervalo)
        horas = int(minutos // 60)
        mins = int(minutos % 60)
        horarios.append(f"{horas:02d}:{mins:02d}")
    
    return horarios


def verificar_conflictos_programacion(programacion, excluir_id=None):
    """
    Verifica conflictos de una programación con otras existentes
    """
    conflictos = []
    
    # Buscar programaciones de la misma cuña
    programaciones_cuña = ProgramacionTransmision.objects.filter(
        cuña=programacion.cuña,
        estado='activa'
    )
    
    if excluir_id:
        programaciones_cuña = programaciones_cuña.exclude(pk=excluir_id)
    
    for otra_prog in programaciones_cuña:
        # Verificar solapamiento de tiempo
        if hay_solapamiento_programaciones(programacion, otra_prog):
            conflictos.append({
                'programacion': otra_prog,
                'tipo': 'solapamiento_tiempo',
                'descripcion': f'Solapamiento de horarios con {otra_prog.codigo}'
            })
    
    return conflictos


def hay_solapamiento_programaciones(prog1, prog2):
    """
    Verifica si dos programaciones se solapan en tiempo
    """
    # Simplificación: verificar si ambas están activas el mismo día
    # En implementación real, sería más complejo según tipo de programación
    
    if prog1.tipo_programacion == 'diaria' and prog2.tipo_programacion == 'diaria':
        return True  # Ambas diarias se solapan
    
    # Más lógica según tipos de programación...
    return False


# ==================== UTILIDADES DE TRANSMISIÓN ====================

def obtener_estadisticas_tiempo_real():
    """
    Obtiene estadísticas en tiempo real con cache
    """
    stats = cache.get('estadisticas_tiempo_real')
    if stats is None:
        ahora = timezone.now()
        inicio_dia = obtener_inicio_dia()
        
        transmisiones_hoy = TransmisionActual.objects.filter(
            inicio_programado__gte=inicio_dia
        )
        
        stats = {
            'transmisiones_hoy': transmisiones_hoy.count(),
            'completadas_hoy': transmisiones_hoy.filter(estado='completada').count(),
            'en_curso': transmisiones_hoy.filter(estado='transmitiendo').count(),
            'con_error': transmisiones_hoy.filter(estado='error').count(),
            'tiempo_total_hoy': transmisiones_hoy.filter(
                duracion_segundos__isnull=False
            ).aggregate(total=Sum('duracion_segundos'))['total'] or 0,
            'timestamp': ahora.isoformat(),
        }
        
        cache.set('estadisticas_tiempo_real', stats, timeout=30)  # 30 segundos
    
    return stats


def calcular_tiempo_aire_disponible():
    """
    Calcula el tiempo de aire disponible restante para hoy
    """
    config = obtener_configuracion_cache()
    if not config:
        return 0
    
    ahora = timezone.now()
    
    # Calcular tiempo total disponible hoy
    if ahora.time() > config.hora_fin_transmision:
        return 0  # Ya terminó el horario de hoy
    
    inicio_hoy = datetime.combine(ahora.date(), config.hora_inicio_transmision)
    fin_hoy = datetime.combine(ahora.date(), config.hora_fin_transmision)
    
    if timezone.is_naive(inicio_hoy):
        inicio_hoy = timezone.make_aware(inicio_hoy)
    if timezone.is_naive(fin_hoy):
        fin_hoy = timezone.make_aware(fin_hoy)
    
    inicio_efectivo = max(ahora, inicio_hoy)
    tiempo_disponible = (fin_hoy - inicio_efectivo).total_seconds()
    
    # Restar tiempo ya ocupado por transmisiones programadas
    transmisiones_futuras = TransmisionActual.objects.filter(
        inicio_programado__gte=inicio_efectivo,
        inicio_programado__lte=fin_hoy,
        estado__in=['preparando', 'transmitiendo']
    )
    
    tiempo_ocupado = sum([
        t.duracion_segundos or 0 
        for t in transmisiones_futuras.filter(duracion_segundos__isnull=False)
    ])
    
    return max(0, tiempo_disponible - tiempo_ocupado)


# ==================== UTILIDADES DE LOGS Y EVENTOS ====================

def crear_log_personalizado(accion, descripcion, **kwargs):
    """
    Crea un log personalizado con datos adicionales
    """
    return LogTransmision.log_evento(
        accion=accion,
        descripcion=descripcion,
        **kwargs
    )


def obtener_resumen_logs(fecha_inicio, fecha_fin):
    """
    Obtiene un resumen de logs por período
    """
    logs = LogTransmision.objects.filter(
        timestamp__range=[fecha_inicio, fecha_fin]
    )
    
    resumen = {
        'total_eventos': logs.count(),
        'por_accion': dict(logs.values('accion').annotate(count=Count('accion')).values_list('accion', 'count')),
        'por_nivel': dict(logs.values('nivel').annotate(count=Count('nivel')).values_list('nivel', 'count')),
        'errores_criticos': logs.filter(nivel='critical').count(),
        'usuarios_activos': logs.values('usuario').distinct().count(),
    }
    
    return resumen


def detectar_patrones_error():
    """
    Detecta patrones en los errores del sistema
    """
    # Últimas 24 horas
    desde = timezone.now() - timedelta(hours=24)
    
    errores = LogTransmision.objects.filter(
        timestamp__gte=desde,
        nivel__in=['error', 'critical']
    )
    
    patrones = {
        'errores_por_hora': {},
        'errores_por_cuña': {},
        'errores_mas_comunes': [],
    }
    
    # Agrupar por hora
    for error in errores:
        hora = error.timestamp.hour
        patrones['errores_por_hora'][hora] = patrones['errores_por_hora'].get(hora, 0) + 1
    
    # Agrupar por cuña
    for error in errores.filter(cuña__isnull=False):
        codigo = error.cuña.codigo
        patrones['errores_por_cuña'][codigo] = patrones['errores_por_cuña'].get(codigo, 0) + 1
    
    # Errores más comunes
    patrones['errores_mas_comunes'] = list(
        errores.values('descripcion')
        .annotate(count=Count('descripcion'))
        .order_by('-count')[:5]
        .values_list('descripcion', 'count')
    )
    
    return patrones


# ==================== UTILIDADES DE VALIDACIÓN ====================

def validar_cuña_para_transmision(cuña):
    """
    Valida si una cuña está lista para transmisión
    """
    errores = []
    
    # Verificar estado
    if cuña.estado not in ['activa', 'aprobada']:
        errores.append(f"Estado inválido: {cuña.estado}")
    
    # Verificar fechas de vigencia
    hoy = timezone.now().date()
    if cuña.fecha_inicio > hoy:
        errores.append("Cuña aún no ha iniciado su período de vigencia")
    
    if cuña.fecha_fin < hoy:
        errores.append("Cuña ya venció")
    
    # Verificar archivo de audio
    if not cuña.archivo_audio:
        errores.append("No tiene archivo de audio")
    elif not cuña.archivo_audio.duracion_segundos:
        errores.append("Archivo de audio sin duración válida")
    
    return len(errores) == 0, errores


def validar_horario_transmision(inicio, fin):
    """
    Valida un horario de transmisión
    """
    errores = []
    
    # Verificar que sea en el futuro
    ahora = timezone.now()
    if inicio <= ahora:
        errores.append("El horario de inicio debe ser en el futuro")
    
    # Verificar que fin sea después de inicio
    if fin <= inicio:
        errores.append("El horario de fin debe ser posterior al inicio")
    
    # Verificar que esté en horario permitido
    config = obtener_configuracion_cache()
    if config:
        if not config.esta_en_horario_transmision(inicio.time()):
            errores.append("Horario de inicio fuera del horario de transmisión")
        
        if not config.esta_en_horario_transmision(fin.time()):
            errores.append("Horario de fin fuera del horario de transmisión")
    
    return len(errores) == 0, errores


# ==================== UTILIDADES DE EXPORT/IMPORT ====================

def exportar_configuracion():
    """
    Exporta la configuración actual a dict
    """
    config = obtener_configuracion_cache()
    if not config:
        return None
    
    return {
        'nombre': config.nombre_configuracion,
        'modo_operacion': config.modo_operacion,
        'horario_inicio': config.hora_inicio_transmision.strftime('%H:%M'),
        'horario_fin': config.hora_fin_transmision.strftime('%H:%M'),
        'intervalo_minimo': config.intervalo_minimo_segundos,
        'duracion_maxima_bloque': config.duracion_maxima_bloque,
        'volumen_base': float(config.volumen_base),
        'configuraciones': {
            'permitir_solapamiento': config.permitir_solapamiento,
            'priorizar_por_pago': config.priorizar_por_pago,
            'reproducir_solo_activas': config.reproducir_solo_activas,
            'verificar_fechas_vigencia': config.verificar_fechas_vigencia,
            'notificar_errores': config.notificar_errores,
            'notificar_inicio_fin': config.notificar_inicio_fin,
        }
    }


def importar_configuracion(datos):
    """
    Importa configuración desde dict
    """
    try:
        config = obtener_configuracion_cache()
        if not config:
            return False, "No hay configuración activa"
        
        # Actualizar campos
        config.nombre_configuracion = datos.get('nombre', config.nombre_configuracion)
        config.modo_operacion = datos.get('modo_operacion', config.modo_operacion)
        
        # Parsear horarios
        horario_inicio = datos.get('horario_inicio')
        if horario_inicio:
            config.hora_inicio_transmision = parsear_horario(horario_inicio)
        
        horario_fin = datos.get('horario_fin')
        if horario_fin:
            config.hora_fin_transmision = parsear_horario(horario_fin)
        
        # Otros campos
        config.intervalo_minimo_segundos = datos.get('intervalo_minimo', config.intervalo_minimo_segundos)
        config.duracion_maxima_bloque = datos.get('duracion_maxima_bloque', config.duracion_maxima_bloque)
        config.volumen_base = Decimal(str(datos.get('volumen_base', config.volumen_base)))
        
        # Configuraciones booleanas
        configuraciones = datos.get('configuraciones', {})
        for campo, valor in configuraciones.items():
            if hasattr(config, campo):
                setattr(config, campo, valor)
        
        config.save()
        
        # Limpiar cache
        cache.delete('configuracion_transmision_activa')
        
        return True, "Configuración importada correctamente"
        
    except Exception as e:
        return False, f"Error importando configuración: {str(e)}"


# ==================== UTILIDADES DE CACHE ====================

def limpiar_cache_transmisiones():
    """
    Limpia todo el cache relacionado con transmisiones
    """
    keys = [
        'configuracion_transmision_activa',
        'transmision_actual',
        'proximas_transmisiones',
        'estadisticas_tiempo_real',
        'sistema_transmision_salud'
    ]
    
    cache.delete_many(keys)


def generar_hash_estado_sistema():
    """
    Genera un hash del estado actual del sistema para detectar cambios
    """
    # Incluir información relevante del estado
    estado = {
        'timestamp': timezone.now().isoformat(),
        'transmisiones_activas': TransmisionActual.objects.filter(estado='transmitiendo').count(),
        'programaciones_activas': ProgramacionTransmision.objects.filter(estado='activa').count(),
        'config_activa': obtener_configuracion_cache() is not None,
    }
    
    estado_str = json.dumps(estado, sort_keys=True)
    return hashlib.md5(estado_str.encode()).hexdigest()


# ==================== UTILIDADES DE DEBUGGING ====================

def debug_estado_sistema():
    """
    Retorna información detallada del estado del sistema para debugging
    """
    info = {
        'timestamp': timezone.now().isoformat(),
        'configuracion': None,
        'transmisiones': {},
        'programaciones': {},
        'cache': {},
        'sistema': {}
    }
    
    # Configuración
    config = obtener_configuracion_cache()
    if config:
        info['configuracion'] = {
            'nombre': config.nombre_configuracion,
            'modo': config.modo_operacion,
            'estado': config.estado_sistema,
            'puede_transmitir': config.puede_transmitir(),
        }
    
    # Transmisiones
    info['transmisiones'] = {
        'activas': TransmisionActual.objects.filter(estado='transmitiendo').count(),
        'preparando': TransmisionActual.objects.filter(estado='preparando').count(),
        'completadas_hoy': TransmisionActual.objects.filter(
            inicio_programado__date=timezone.now().date(),
            estado='completada'
        ).count(),
    }
    
    # Programaciones
    info['programaciones'] = {
        'activas': ProgramacionTransmision.objects.filter(estado='activa').count(),
        'programadas': ProgramacionTransmision.objects.filter(estado='programada').count(),
    }
    
    # Estado del cache
    info['cache'] = {
        'config_cached': cache.get('configuracion_transmision_activa') is not None,
        'stats_cached': cache.get('estadisticas_tiempo_real') is not None,
        'transmision_cached': cache.get('transmision_actual') is not None,
    }
    
    # Sistema
    info['sistema'] = {
        'tiempo_aire_disponible': calcular_tiempo_aire_disponible(),
        'en_horario_transmision': esta_en_horario_transmision(),
        'hash_estado': generar_hash_estado_sistema(),
    }
    
    return info