"""
Shared authentication / authorization helpers.

Every protected route should use @token_required (must be logged in) and,
where a role restriction applies, @roles_required('Admin', ...) as well.

Usage:
    from utils.auth import token_required, roles_required

    @patient_bp.route('/patients', methods=['GET'])
    @token_required
    def get_patients():
        ...

    @patient_bp.route('/patients', methods=['DELETE'])
    @token_required
    @roles_required('Admin', 'Receptionist')
    def delete_patient(id):
        ...

Inside a protected view, the authenticated user is available as
`request.current_user`, a dict with at least `user_id` and `role`
(the same payload that was encoded into the JWT at login).
"""
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def _decode_token():
    """Pull the bearer token out of the Authorization header and decode it.

    Returns the decoded payload dict, or raises ValueError with a message
    suitable for returning to the client.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        raise ValueError('Missing token')

    parts = auth_header.split(' ')
    if len(parts) != 2 or parts[0] != 'Bearer':
        raise ValueError('Invalid Authorization header format. Expected: Bearer <token>')

    token = parts[1]
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'],
        )
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')

    return payload


def token_required(f):
    """Require a valid JWT. Populates request.current_user on success."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            payload = _decode_token()
        except ValueError as e:
            return jsonify({'error': str(e)}), 401

        request.current_user = payload
        g.current_user = payload
        return f(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    """Restrict a route to specific roles. Must be stacked under @token_required
    (i.e. @token_required goes above this in the decorator list, since
    decorators apply bottom-up)."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if current_user is None:
                # Defensive: roles_required used without token_required.
                return jsonify({'error': 'Missing token'}), 401

            if current_user.get('role') not in allowed_roles:
                return jsonify({
                    'error': f"Unauthorized: requires one of roles {list(allowed_roles)}"
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
