"""
Módulo para configuração de logging centralizado.

Este módulo configura o logging para toda a aplicação, garantindo
formato consistente e captura detalhada de informações para diagnóstico.
"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuração de níveis de log
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configurar logger raiz
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL))

# Limpar handlers existentes para evitar duplicação
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Adicionar handler para stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
root_logger.addHandler(console_handler)

# Logger específico para este módulo
logger = logging.getLogger(__name__)

class StructuredLogRecord(logging.LogRecord):
    """
    Extensão de LogRecord para suportar logging estruturado.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structured_data = {}

class StructuredLogger(logging.Logger):
    """
    Logger que suporta logging estruturado com metadados adicionais.
    """
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """
        Cria um registro de log estruturado.
        """
        record = StructuredLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                if key == 'structured_data':
                    record.structured_data = extra[key]
                else:
                    setattr(record, key, extra[key])
        return record

    def structured_log(self, level: int, msg: str, structured_data: Dict[str, Any], *args, **kwargs):
        """
        Registra uma mensagem com dados estruturados adicionais.
        
        Args:
            level: Nível de log (INFO, WARNING, ERROR, etc.)
            msg: Mensagem de log
            structured_data: Dicionário com dados estruturados adicionais
            *args, **kwargs: Argumentos adicionais para o logger
        """
        if not self.isEnabledFor(level):
            return
            
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['structured_data'] = structured_data
        
        self._log(level, msg, args, **kwargs)

class StructuredFormatter(logging.Formatter):
    """
    Formatador que inclui dados estruturados no formato JSON.
    """
    def format(self, record):
        """
        Formata o registro de log, incluindo dados estruturados.
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        
        # Adicionar dados estruturados se disponíveis
        if hasattr(record, 'structured_data') and record.structured_data:
            log_data['data'] = record.structured_data
            
        # Adicionar informações de exceção se disponíveis
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data)

def get_logger(name: str) -> StructuredLogger:
    """
    Obtém um logger estruturado para o módulo especificado.
    
    Args:
        name: Nome do módulo
        
    Returns:
        Logger estruturado configurado
    """
    # Registrar a classe de logger personalizada
    logging.setLoggerClass(StructuredLogger)
    
    # Obter logger para o módulo
    logger = logging.getLogger(name)
    
    # Configurar nível de log
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    return logger

def configure_json_logging():
    """
    Configura logging no formato JSON para ambientes de produção.
    """
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Adicionar handler com formatador JSON
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(json_handler)
    
    logger.info("Logging JSON configurado para ambiente de produção")

# Configurar logging JSON em produção
if os.environ.get("ENVIRONMENT", "").lower() == "production":
    configure_json_logging()
    
logger.info(f"Módulo de logging inicializado com nível {LOG_LEVEL}")
