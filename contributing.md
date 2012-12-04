Contributing to Malt.io
=======================
The following guidelines should be followed when contributing to Malt.io.

Create a Fork
-------------
Begin by creating a fork of Malt.io and applying your changes there. See:

 * https://help.github.com/articles/fork-a-repo

Rebase Latest Head
------------------
Make sure your clone has the latest changes from master before you begin your pull request.

```bash
git pull --rebase upstream master
```

Rebasing ensures that your changes are applied in the correct order and a big monolithic merge is avoided.

Unit Tests
----------
Please make sure to run unit tests before sending a pull request. Code that fails the unit tests will not be merged.

```bash
./runTests.sh
```

License
-------
Any changes that are accepted will be licensed under the same license as the rest of Malt.io, which can be found in the readme.
