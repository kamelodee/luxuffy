import requests
import uuid
from django.conf import settings
from django.urls import reverse
from typing import Dict, Any, Optional


class PaystackAPI:
    """Paystack payment gateway integration"""
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = 'https://api.paystack.co'
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Paystack API"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def initialize_transaction(
        self,
        email: str,
        amount: float,
        reference: Optional[str] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a payment transaction"""
        if not reference:
            reference = str(uuid.uuid4())
        
        data = {
            'email': email,
            'amount': int(amount * 100),  # Convert to kobo
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {}
        }
        
        return self._make_request('POST', 'transaction/initialize', data)
    
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a payment transaction"""
        return self._make_request('GET', f'transaction/verify/{reference}')
    
    def list_transactions(
        self,
        per_page: int = 50,
        page: int = 1,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """List transactions"""
        endpoint = f'transaction?perPage={per_page}&page={page}'
        if from_date:
            endpoint += f'&from={from_date}'
        if to_date:
            endpoint += f'&to={to_date}'
        
        return self._make_request('GET', endpoint)
    
    def get_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Get details of a transaction"""
        return self._make_request('GET', f'transaction/{transaction_id}')
    
    def create_refund(
        self,
        transaction_reference: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a refund"""
        data = {'transaction': transaction_reference}
        if amount:
            data['amount'] = int(amount * 100)  # Convert to kobo
        
        return self._make_request('POST', 'refund', data)
    
    def list_refunds(
        self,
        per_page: int = 50,
        page: int = 1,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """List refunds"""
        endpoint = f'refund?perPage={per_page}&page={page}'
        if from_date:
            endpoint += f'&from={from_date}'
        if to_date:
            endpoint += f'&to={to_date}'
        
        return self._make_request('GET', endpoint)
    
    def get_refund(self, refund_reference: str) -> Dict[str, Any]:
        """Get details of a refund"""
        return self._make_request('GET', f'refund/{refund_reference}')
