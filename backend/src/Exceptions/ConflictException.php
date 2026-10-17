<?php
declare(strict_types=1);

namespace Aurora\Exceptions;

final class ConflictException extends ApiException
{
    public function __construct(array $payload)
    {
        parent::__construct(409, ['ok' => false] + $payload);
    }
}
