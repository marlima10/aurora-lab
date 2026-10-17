<?php
declare(strict_types=1);

namespace Aurora\Exceptions;

final class ValidationException extends ApiException
{
    public function __construct(string $message)
    {
        parent::__construct(400, ['ok' => false, 'error' => $message]);
    }
}
