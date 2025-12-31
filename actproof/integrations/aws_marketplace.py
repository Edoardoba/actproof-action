"""
Integrazione AWS Marketplace
Implementa ResolveCustomer e BatchMeterUsage per billing
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import json


class MeteringRecord(BaseModel):
    """Record di metering per AWS Marketplace"""
    
    customer_identifier: str = Field(..., description="Customer ID o Registration Token")
    dimension: str = Field(..., description="Dimensione di pricing (es. 'scan', 'compliance_check')")
    quantity: int = Field(..., description="Quantità da fatturare")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp operazione")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_identifier": "12345678-1234-1234-1234-123456789012",
                "dimension": "scan",
                "quantity": 1,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class AWSMarketplaceClient:
    """
    Client per integrazione AWS Marketplace
    Gestisce ResolveCustomer e BatchMeterUsage
    """
    
    def __init__(
        self,
        product_code: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Inizializza client AWS Marketplace
        
        Args:
            product_code: Codice prodotto AWS Marketplace
            region: Regione AWS (default: us-east-1)
            aws_access_key_id: AWS Access Key ID (opzionale, usa credenziali di default)
            aws_secret_access_key: AWS Secret Access Key (opzionale)
        """
        self.product_code = product_code
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        self._check_dependencies()
        self._init_client()
    
    def _check_dependencies(self):
        """Verifica che boto3 sia disponibile"""
        try:
            import boto3
            self.boto3_available = True
        except ImportError:
            self.boto3_available = False
            print("⚠️  boto3 non disponibile. Installa con: pip install boto3")
    
    def _init_client(self):
        """Inizializza client AWS Marketplace Metering"""
        if not self.boto3_available:
            self.client = None
            return
        
        try:
            import boto3
            from botocore.config import Config
            
            config = Config(region_name=self.region)
            
            if self.aws_access_key_id and self.aws_secret_access_key:
                self.client = boto3.client(
                    'meteringmarketplace',
                    region_name=self.region,
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    config=config,
                )
            else:
                # Usa credenziali di default (IAM role, env vars, etc.)
                self.client = boto3.client(
                    'meteringmarketplace',
                    region_name=self.region,
                    config=config,
                )
        except Exception as e:
            print(f"⚠️  Errore inizializzazione client AWS: {e}")
            self.client = None
    
    def resolve_customer(self, registration_token: str) -> Dict[str, Any]:
        """
        Risolve registration token in customer identifier permanente
        
        Args:
            registration_token: Token di registrazione dal cliente
        
        Returns:
            Dict con customer_identifier e product_code
        
        Raises:
            Exception: Se il client AWS non è disponibile o errore API
        """
        if not self.client:
            raise RuntimeError("Client AWS Marketplace non disponibile. Verifica installazione boto3.")
        
        try:
            response = self.client.resolve_customer(
                RegistrationToken=registration_token
            )
            
            return {
                "customer_identifier": response.get("CustomerIdentifier"),
                "product_code": response.get("ProductCode"),
                "resolved_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            raise RuntimeError(f"Errore ResolveCustomer: {e}")
    
    def batch_meter_usage(
        self,
        records: List[MeteringRecord],
    ) -> Dict[str, Any]:
        """
        Invia record di metering in batch ad AWS Marketplace
        
        Args:
            records: Lista di record di metering
        
        Returns:
            Dict con risultati (successi/fallimenti)
        
        Raises:
            Exception: Se il client AWS non è disponibile o errore API
        """
        if not self.client:
            raise RuntimeError("Client AWS Marketplace non disponibile. Verifica installazione boto3.")
        
        if not records:
            return {"success": True, "results": []}
        
        try:
            # Prepara usage records per AWS API
            usage_records = []
            for record in records:
                usage_records.append({
                    "Timestamp": record.timestamp,
                    "CustomerIdentifier": record.customer_identifier,
                    "Dimension": record.dimension,
                    "Quantity": record.quantity,
                })
            
            # Chiama BatchMeterUsage
            response = self.client.batch_meter_usage(
                ProductCode=self.product_code,
                UsageRecords=usage_records,
            )
            
            # Processa risultati
            results = []
            for result in response.get("Results", []):
                results.append({
                    "usage_record": result.get("UsageRecord"),
                    "metering_record_id": result.get("MeteringRecordId"),
                    "status": result.get("Status"),  # Success, CustomerNotSubscribed, DuplicateRecord
                })
            
            return {
                "success": True,
                "results": results,
                "unprocessed_records": response.get("UnprocessedRecords", []),
            }
        except Exception as e:
            raise RuntimeError(f"Errore BatchMeterUsage: {e}")
    
    def meter_usage(
        self,
        customer_identifier: str,
        dimension: str,
        quantity: int = 1,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method per metering singolo
        
        Args:
            customer_identifier: Customer ID
            dimension: Dimensione pricing
            quantity: Quantità
            timestamp: Timestamp (default: now)
        
        Returns:
            Risultato metering
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        record = MeteringRecord(
            customer_identifier=customer_identifier,
            dimension=dimension,
            quantity=quantity,
            timestamp=timestamp,
        )
        
        return self.batch_meter_usage([record])
    
    def create_metering_record(
        self,
        customer_identifier: str,
        operation_type: str,
        quantity: int = 1,
    ) -> MeteringRecord:
        """
        Crea record di metering per operazione
        
        Args:
            customer_identifier: Customer ID
            operation_type: Tipo operazione ('scan', 'compliance_check', 'fairness_audit', etc.)
            quantity: Quantità
        
        Returns:
            MeteringRecord
        """
        # Mappa operazioni a dimensioni pricing
        dimension_map = {
            "scan": "repository_scan",
            "compliance_check": "compliance_evaluation",
            "fairness_audit": "bias_audit",
            "report_generation": "legal_report",
        }
        
        dimension = dimension_map.get(operation_type, operation_type)
        
        return MeteringRecord(
            customer_identifier=customer_identifier,
            dimension=dimension,
            quantity=quantity,
            timestamp=datetime.utcnow(),
        )
