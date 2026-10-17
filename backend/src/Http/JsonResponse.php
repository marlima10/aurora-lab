<?php
declare(strict_types=1);

namespace Aurora\Http;

final class JsonResponse
{
    public function __construct(public readonly int $status, public readonly array $data) {}

    public function send(): void
    {
        $json = json_encode($this->data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        http_response_code($this->status);
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store, no-cache, must-revalidate');
        header('X-Content-Type-Options: nosniff');
        echo $json;
    }
}
