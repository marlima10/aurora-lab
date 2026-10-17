<?php
declare(strict_types=1);

namespace Aurora\Exceptions;

use RuntimeException;

class ApiException extends RuntimeException
{
    public function __construct(public readonly int $status, public readonly array $payload)
    {
        parent::__construct($payload['error'] ?? 'Falha na operação');
    }
}
