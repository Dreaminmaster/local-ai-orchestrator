function main() {
  try {
    require("some-fake-npm-package-xyz");
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
}
main();
