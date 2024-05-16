import os
import pynetbox
import unittest

from dotenv import load_dotenv

class DevNetboxTestFunctions(unittest.TestCase):

    def test_connection(self):
        load_dotenv()
        api_token = os.environ.get("dev_nb_token")
        nb = pynetbox.api(url="https://netbox-dev.mke.cnty", token=api_token)
        
        result = nb.users.users.get(1)

        self.assertEqual(result.username, "HurdaDakotah")

if __name__ == '__main__': 
    unittest.main()