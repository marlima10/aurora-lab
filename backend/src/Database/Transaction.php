<?php
declare(strict_types=1);

namespace Aurora\Database;

use PDO;
use Throwable;

final class Transaction
{
    public function __construct(private PDO $db) {}

    public function run(callable $operation): mixed
    {
        // BEGIN IMMEDIATE preserva o bloqueio usado pelo controle de revisões.
        $this->db->exec('BEGIN IMMEDIATE');
        try {
            $result = $operation();
            $this->db->exec('COMMIT');
            return $result;
        } catch (Throwable $error) {
            $this->db->exec('ROLLBACK');
            throw $error;
        }
    }
}
