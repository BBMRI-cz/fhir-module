import { logout } from "../logout";

import { signOut } from "../../../../auth";

jest.mock("../../../../auth", () => ({
  signOut: jest.fn(),
}));

describe("logout", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should call signOut with correct redirect", async () => {
    (signOut as jest.Mock).mockResolvedValue(undefined);

    await logout();

    expect(signOut).toHaveBeenCalledWith({
      redirectTo: "/login",
    });
  });

  it("should call signOut exactly once", async () => {
    (signOut as jest.Mock).mockResolvedValue(undefined);

    await logout();

    expect(signOut).toHaveBeenCalledTimes(1);
  });

  it("should handle signOut errors", async () => {
    (signOut as jest.Mock).mockRejectedValue(new Error("Sign out failed"));

    await expect(logout()).rejects.toThrow("Sign out failed");
  });
});
