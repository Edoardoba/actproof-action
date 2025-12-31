"""
Middleware Audit Trail
Cattura ogni interazione e crea audit trail immutabile
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum
import json
import hashlib
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Tipi di eventi audit"""
    SCAN = "scan"
    COMPLIANCE_CHECK = "compliance_check"
    FAIRNESS_AUDIT = "fairness_audit"
    REPORT_GENERATION = "report_generation"
    API_REQUEST = "api_request"
    USER_ACTION = "user_action"


class AuditLog(BaseModel):
    """Log entry per audit trail"""
    
    event_id: str = Field(..., description="ID univoco evento")
    event_type: AuditEventType = Field(..., description="Tipo evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp evento")
    
    # Informazioni utente/cliente
    user_id: Optional[str] = Field(None, description="ID utente")
    customer_id: Optional[str] = Field(None, description="ID cliente AWS Marketplace")
    session_id: Optional[str] = Field(None, description="ID sessione")
    
    # Dettagli operazione
    operation: str = Field(..., description="Operazione eseguita")
    resource_id: Optional[str] = Field(None, description="ID risorsa interessata")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Dati input")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Dati output")
    
    # Risultato
    success: bool = Field(..., description="Se operazione riuscita")
    error_message: Optional[str] = Field(None, description="Messaggio errore se fallita")
    
    # Metadati
    ip_address: Optional[str] = Field(None, description="IP address richiesta")
    user_agent: Optional[str] = Field(None, description="User agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati aggiuntivi")
    
    # Hash per immutabilità
    previous_hash: Optional[str] = Field(None, description="Hash log precedente")
    hash: Optional[str] = Field(None, description="Hash questo log")
    
    def compute_hash(self) -> str:
        """Calcola hash SHA-256 per immutabilità"""
        # Crea stringa da hashare (escludi hash stesso)
        data_str = json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "operation": self.operation,
            "resource_id": self.resource_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "success": self.success,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def model_post_init(self, __context):
        """Calcola hash dopo inizializzazione"""
        if not self.hash:
            self.hash = self.compute_hash()


class AuditMiddleware:
    """
    Middleware per audit trail immutabile
    Logga ogni interazione per compliance e tracciabilità
    """
    
    def __init__(
        self,
        audit_log_path: Optional[Path] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = False,
    ):
        """
        Inizializza middleware audit
        
        Args:
            audit_log_path: Percorso file log (default: logs/audit.log)
            enable_file_logging: Abilita logging su file
            enable_console_logging: Abilita logging su console
        """
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging
        
        if audit_log_path is None:
            audit_log_path = Path("logs/audit.log")
        
        self.audit_log_path = Path(audit_log_path)
        if enable_file_logging:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Carica ultimo hash per catena immutabile
        self.last_hash = self._load_last_hash()
    
    def _load_last_hash(self) -> Optional[str]:
        """Carica hash ultimo log per catena immutabile"""
        if not self.audit_log_path.exists():
            return None
        
        try:
            # Leggi ultima riga (JSON)
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        log_data = json.loads(last_line)
                        return log_data.get("hash")
        except Exception as e:
            print(f"⚠️  Errore caricamento ultimo hash: {e}")
        
        return None
    
    def log_event(
        self,
        event_type: AuditEventType,
        operation: str,
        success: bool = True,
        user_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Logga evento nel audit trail
        
        Args:
            event_type: Tipo evento
            operation: Operazione eseguita
            success: Se operazione riuscita
            user_id: ID utente
            customer_id: ID cliente
            session_id: ID sessione
            resource_id: ID risorsa
            input_data: Dati input
            output_data: Dati output
            error_message: Messaggio errore
            ip_address: IP address
            user_agent: User agent
            metadata: Metadati aggiuntivi
        
        Returns:
            AuditLog creato
        """
        import uuid
        
        # Genera ID evento univoco
        event_id = str(uuid.uuid4())
        
        # Crea log entry
        audit_log = AuditLog(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            customer_id=customer_id,
            session_id=session_id,
            operation=operation,
            resource_id=resource_id,
            input_data=input_data or {},
            output_data=output_data or {},
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            previous_hash=self.last_hash,
        )
        
        # Calcola hash
        audit_log.hash = audit_log.compute_hash()
        
        # Salva log
        self._save_log(audit_log)
        
        # Aggiorna ultimo hash
        self.last_hash = audit_log.hash
        
        return audit_log
    
    def _save_log(self, audit_log: AuditLog):
        """Salva log su file e/o console"""
        log_json = audit_log.model_dump(mode="json")
        
        if self.enable_file_logging:
            try:
                # Append su file (una riga JSON per entry)
                with open(self.audit_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_json) + "\n")
            except Exception as e:
                print(f"⚠️  Errore salvataggio audit log: {e}")
        
        if self.enable_console_logging:
            print(f"[AUDIT] {audit_log.event_type.value} | {audit_log.operation} | Success: {audit_log.success}")
    
    def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Recupera audit trail con filtri
        
        Args:
            user_id: Filtra per user ID
            customer_id: Filtra per customer ID
            event_type: Filtra per tipo evento
            start_date: Data inizio
            end_date: Data fine
            limit: Limite risultati
        
        Returns:
            Lista AuditLog
        """
        if not self.audit_log_path.exists():
            return []
        
        logs = []
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        log_data = json.loads(line)
                        audit_log = AuditLog(**log_data)
                        
                        # Applica filtri
                        if user_id and audit_log.user_id != user_id:
                            continue
                        if customer_id and audit_log.customer_id != customer_id:
                            continue
                        if event_type and audit_log.event_type != event_type:
                            continue
                        if start_date and audit_log.timestamp < start_date:
                            continue
                        if end_date and audit_log.timestamp > end_date:
                            continue
                        
                        logs.append(audit_log)
                        
                        if len(logs) >= limit:
                            break
                    except Exception as e:
                        print(f"⚠️  Errore parsing log entry: {e}")
                        continue
        except Exception as e:
            print(f"⚠️  Errore lettura audit log: {e}")
        
        return logs
    
    def verify_audit_trail_integrity(self) -> Dict[str, Any]:
        """
        Verifica integrità audit trail (catena hash)
        
        Returns:
            Dict con risultati verifica
        """
        if not self.audit_log_path.exists():
            return {"valid": True, "message": "No audit log file"}
        
        logs = []
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        log_data = json.loads(line)
                        logs.append(AuditLog(**log_data))
        except Exception as e:
            return {"valid": False, "error": str(e)}
        
        if not logs:
            return {"valid": True, "message": "Empty audit log"}
        
        # Verifica catena hash
        previous_hash = None
        invalid_count = 0
        
        for i, log in enumerate(logs):
            # Verifica hash precedente
            if previous_hash and log.previous_hash != previous_hash:
                invalid_count += 1
            
            # Verifica hash corrente
            computed_hash = log.compute_hash()
            if computed_hash != log.hash:
                invalid_count += 1
            
            previous_hash = log.hash
        
        return {
            "valid": invalid_count == 0,
            "total_logs": len(logs),
            "invalid_entries": invalid_count,
            "integrity_check": "PASSED" if invalid_count == 0 else "FAILED",
        }
