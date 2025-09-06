export class DatabaseError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = "DatabaseError";
  }
}

export class UserNotFoundError extends Error {
  constructor(identifier: string | number) {
    super(`User not found: ${identifier}`);
    this.name = "UserNotFoundError";
  }
}

export class UserCreationError extends DatabaseError {
  constructor(username: string, cause?: unknown) {
    super(`Failed to create user: ${username}`, cause);
    this.name = "UserCreationError";
  }
}

export class InvalidCredentialsError extends Error {
  constructor() {
    super("Invalid username or password");
    this.name = "InvalidCredentialsError";
  }
}

export class AuthenticationError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = "AuthenticationError";
  }
}
